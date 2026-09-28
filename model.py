from pathlib import Path
from urllib.parse import urlsplit
import math,zipfile,xml.etree.ElementTree as ET
import numpy as np,qrcode,trimesh,zxingcpp
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
def normalize(text):
 text=text.strip()
 if not text or len(text)>500:raise ValueError('Enter a website link of 1–500 characters.')
 if '://' not in text:text='https://'+text
 p=urlsplit(text)
 _=p.port
 if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or any(c.isspace() for c in text):raise ValueError('Use an http or https website link without spaces or login credentials.')
 return text

def meshpoly(poly,h,z=0):
 m=trimesh.creation.extrude_polygon(poly,h,engine='triangle');m.apply_translation([0,0,z]);return m

def make3mf(path,base,qr):
 ET.register_namespace('',NS);root=ET.Element('{%s}model'%NS,unit='millimeter');res=ET.SubElement(root,'resources');mat=ET.SubElement(res,'basematerials',id='1')
 for name,color in [('Light base','#FFFFFFFF'),('Dark QR','#111111FF')]:ET.SubElement(mat,'base',name=name,displaycolor=color)
 for ident,mesh,col,name in [(2,base,0,'Base and grip'),(3,qr,1,'QR pattern')]:
  ob=ET.SubElement(res,'object',id=str(ident),type='model',name=name,pid='1',pindex=str(col));mm=ET.SubElement(ob,'mesh');vv=ET.SubElement(mm,'vertices');ff=ET.SubElement(mm,'triangles')
  for x,y,z in mesh.vertices:ET.SubElement(vv,'vertex',x=f'{x:.6f}',y=f'{y:.6f}',z=f'{z:.6f}')
  for a,b,c in mesh.faces:ET.SubElement(ff,'triangle',v1=str(a),v2=str(b),v3=str(c))
 assembly=ET.SubElement(res,'object',id='4',type='model',name='QR assembly');cc=ET.SubElement(assembly,'components')
 for ident in [2,3]:ET.SubElement(cc,'component',objectid=str(ident))
 ET.SubElement(ET.SubElement(root,'build'),'item',objectid='4')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
  z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')

def generate(folder,url,diameter=35,grip=True,style="hollow"):
 url=normalize(url);diameter=float(diameter)
 if not 35<=diameter<=150:raise ValueError('Choose a diameter between 35 and 150 mm.')
 code=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,border=0);code.add_data(url);code.make(fit=True);a=np.array(code.get_matrix());n=len(a)
 # Solid mode reserves a four-module quiet zone; decorative hollow mode uses more of the disc.
 padding=2 if style=="hollow" else 8
 module=(diameter-2)/(math.sqrt(2)*(n+padding))
 minimum=.6 if style=='hollow' else .8
 if module<minimum:raise ValueError(f'This link is too detailed at {diameter:g} mm for the 0.4 mm nozzle. Increase diameter to at least {math.ceil(2+minimum*math.sqrt(2)*(n+padding))} mm or use a shorter URL.')
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);base=meshpoly(Point(0,0).buffer(diameter/2,resolution=96),.56);half=n*module/2
 if style not in ('hollow','solid'):raise ValueError('Unknown model style.')
 if style=='hollow':
  disk=Point(0,0).buffer(diameter/2,resolution=96);ring=disk.difference(Point(0,0).buffer(diameter/2-1.2,resolution=96));ribs=[ring]
  for i in range(n+1):
   t=-half+i*module;ribs += [box(-half-.2,t-.2,half+.2,t+.2),box(t-.2,-half-.2,t+.2,half+.2)]
  for angle in np.pi/4+np.arange(4)*np.pi/2:
   start=(half*np.sign(np.cos(angle)),half*np.sign(np.sin(angle)));end=((diameter/2-.6)*np.cos(angle),(diameter/2-.6)*np.sin(angle));ribs.append(LineString([start,end]).buffer(.5))
  base=meshpoly(unary_union(ribs).buffer(.0001),.56)
 chunks=[]
 for row,col in zip(*np.where(a)):
  # Microscopic gap avoids non-manifold diagonal point contacts.
  chunks.append(meshpoly(box(-half+col*module+.001,half-(row+1)*module+.001,-half+(col+1)*module-.001,half-row*module-.001),.28,.56))
 qr=trimesh.util.concatenate(chunks)
 if grip:
  x=diameter/2-2.;pieces=[base]
  def block(lo,hi):
   m=trimesh.creation.box(extents=np.array(hi)-lo);m.apply_translation((np.array(hi)+lo)/2);return m
  # Peripheral foot patches leave QR + quiet zone untouched as far as practical.
  for sign in [-1,1]:
   yl,yh=(-12.4,-10) if sign<0 else (10,12.4)
   pieces.append(block([x-6,yl,0],[x+1,yh,.84]));pieces.append(block([x-1.4,yl,0],[x+1.4,yh,11.12]))
  pieces.append(block([x-1.4,-12.4,10],[x+1.4,12.4,11.12]));base=trimesh.boolean.union(pieces,engine='manifold')
 if not base.is_watertight or len(base.split())!=1:raise ValueError('The selected geometry does not join safely. Try a larger diameter or disable the grip.')
 # Validate the encoded QR image independently of physical material/lighting.
 preview=qrcode.make(url,error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=12,border=4).convert('RGB');decoded=zxingcpp.read_barcode(np.asarray(preview))
 if not decoded or decoded.text!=url:raise ValueError('QR image failed its scan check.')
 preview.save(folder/'qr.png');base.export(folder/'base.stl');qr.export(folder/'qr_pattern.stl');make3mf(folder/'QR_project.3mf',base,qr)
 # STL is a combined surface assembly; Bambu merges touching parts during slicing.
 trimesh.util.concatenate([base,qr]).export(folder/'QR_single_color.stl')
 (folder/'PRINT_README.txt').write_text(f'''URL: {url}\nDiameter: {diameter:g}mm; modules: {n}; module pitch: {module:.3f}mm\nBase 0.56mm + raised QR 0.28mm. Garage grip: {grip}.\nQR_project.3mf contains a light base and dark QR as one assembly. Color metadata is a suggestion: confirm material assignment in Bambu Studio, select A1, correct nozzle, material and plate, then slice. This is not a pre-sliced print job.\nModel style: {style}. Hollow style includes visible connecting ribs and is decorative, not scan-verified. With only black filament, this is a relief prototype: scanning is not guaranteed. For reliable contrast, use a light base and dark QR or apply contrasting color after printing. Garage grip may obstruct oblique views and needs a physical bridge/strength test.\nThe separate base.stl and qr_pattern.stl share coordinates: load together as parts of a single object; do not auto-arrange independently. QR_single_color.stl combines those surfaces for a one-color print.\nThe PNG was decoded successfully; no physical print scan test has been performed. No print was sent to a printer.\n''')
 return dict(url=url,diameter=diameter,modules=n,module_mm=round(module,2),grip=grip,style=style,digital_scan='passed')
