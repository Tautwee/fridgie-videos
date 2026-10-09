import pathlib
import os
D=pathlib.Path(__file__).resolve().parent
APP=pathlib.Path(os.environ.get('FRIDGIE_APP_HTML', str(D/'app/index.html')))
FONTCSS="".join(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(https://fonts.local/{fam.replace(' ','')}-{w}.woff2) format('woff2');}}" for fam,w in [('Gabarito',600),('Gabarito',800),('Atkinson Hyperlegible',400),('Atkinson Hyperlegible',700)])
async def route(r):
    u=r.request.url
    if u.startswith('https://myfridgie.netlify.app'): return await r.fulfill(path=str(APP),content_type='text/html')
    if u.startswith('https://stage.local'): return await r.fulfill(path=str(D/'stage.html'),content_type='text/html')
    if 'fonts.googleapis.com' in u: return await r.fulfill(body=FONTCSS,content_type='text/css')
    if u.startswith('https://fonts.local/'): return await r.fulfill(path=str(D/'fonts'/u.split('/')[-1]),content_type='font/woff2')
    return await r.abort()
SEED="""() => { const d=(n)=>{const x=new Date();x.setDate(x.getDate()+n);return x.toISOString().slice(0,10)};
 const L=[['Chicken',{expires:d(1)}],['Lettuce',{expires:d(2)}],['Tortilla wraps',{expires:d(9)}],['Greek yogurt',{expires:d(5)}],['Milk',{expires:d(6)}],['Eggs',{expires:d(14)}],['Tomatoes',{expires:d(5)}],['Cheddar',{expires:d(20)}],['Orange juice',{expires:d(4)}],['Ketchup',{}]];
 localStorage.clear(); localStorage.setItem('fridgie-intro','1'); localStorage.setItem('fridgie-streak',JSON.stringify({from:d(-9)})); localStorage.setItem('fridgie-saved',JSON.stringify({m:d(0).slice(0,7),ate:11,toss:0,saved:17})); localStorage.setItem('fridge-shelf-items', JSON.stringify(L.map(([n,o])=>makeItem(n,o)))); }"""

SEED2="""() => { const d=(n)=>{const x=new Date();x.setDate(x.getDate()+n);return x.toISOString().slice(0,10)};
 const F=[['Chicken',1],['Lettuce',2],['Greek yogurt',5],['Milk',6],['Eggs',14],['Cheddar',20],['Butter',25],['Salmon',2],['Ham',4],['Tomatoes',5],['Peppers',8],['Carrots',18],['Cucumber',6],['Strawberries',3],['Apples',16],['Bananas',4],['Orange juice',4],['Cola',60],['Ketchup',null],['Pesto',null],['Hummus',5],['Tortilla wraps',9],['Bread',4],['Leftover pasta',2]];
 const Z=[['Ice cream'],['Burgers'],['Frozen peas'],['Fries'],['Pizza'],['Dumplings'],['Fish fingers'],['Frozen berries'],['Chicken nuggets'],['Spinach']];
 const P=[['Crisps'],['Pasta'],['Rice'],['Tinned tomatoes'],['Honey'],['Peanut butter'],['Cereal'],['Nuts'],['Popcorn'],['Olive oil'],['Chocolate'],['Oats'],['Tuna tins'],['Noodles'],['Soy sauce'],['Biscuits']];
 const items=[...F.map(([n,e])=>makeItem(n,e==null?{}:{expires:d(e)})), ...Z.map(([n])=>makeItem(n,{space:'freezer',group:n==='Spinach'?'veg':undefined})), ...P.map(([n])=>makeItem(n,{space:'pantry'}))];
 localStorage.clear(); localStorage.setItem('fridgie-intro','1'); localStorage.setItem('fridgie-streak',JSON.stringify({from:d(-9)})); localStorage.setItem('fridgie-saved',JSON.stringify({m:d(0).slice(0,7),ate:11,toss:0,saved:17}));
 localStorage.setItem('fridge-shelf-items', JSON.stringify(items));
 localStorage.setItem('fridgie-shop', JSON.stringify(['Milk','Bread','Orange juice','Eggs'].map((n,i)=>({id:'s'+i,name:n,done:false,added:new Date().toISOString()})))); }"""
