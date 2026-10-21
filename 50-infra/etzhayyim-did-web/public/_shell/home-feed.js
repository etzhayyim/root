/* Tree of Life — original procedural artwork, rendered locally with Three.js.
 * This authored source is bundled by build:assets and served from this origin.
 * No external assets, analytics, remote rendering or network requests.
 */
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

(() => {
  const canvas=document.getElementById('life-canvas');
  const stage=document.querySelector('.cosmic-home');
  if(!canvas||!stage)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const compact=matchMedia('(max-width: 820px)').matches;
  let renderer;
  try {
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'low-power'});
    renderer.toneMapping=THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure=.72;
  } catch {return;} // The static Tree of Life remains usable without WebGL 2.
  let randomState = 709231;
  const random = () => {
    randomState = (Math.imul(randomState, 1664525) + 1013904223) >>> 0;
    return randomState / 4294967296;
  };
  const add = (a,b) => a.map((v,i) => v+b[i]);
  const mul = (a,s) => a.map(v => v*s);
  const mix = (a,b,t) => a.map((v,i) => v+(b[i]-v)*t);
  const unit = a => mul(a, 1 / (Math.hypot(...a) || 1));
  const cross = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const gold = [0.86,0.52,0.27];
  const pearl = [0.52,0.88,0.91];
  const rose = [0.78,0.48,0.61];
  const mesh = [];
  const buds = [];
  const dust = [];
  const sparks = [];
  const filaments = [];
  const point = (out,p,c,size,phase) => out.push(...p,...c,size,phase);
  const tube = (path,radius,color,phase) => {
    const sides = compact ? 5 : 7;
    const rings = path.map((p,i) => {
      const tangent = unit(path[Math.min(path.length-1,i+1)].map((v,j) => v-path[Math.max(0,i-1)][j]));
      const normal = unit(cross(tangent, Math.abs(tangent[1]) > .92 ? [1,0,0] : [0,1,0]));
      const binormal = cross(tangent,normal);
      const r = radius * (1 - .46 * i / (path.length-1));
      return Array.from({length:sides}, (_,j) => {
        const angle = j / sides * Math.PI * 2;
        const n = add(mul(normal,Math.cos(angle)),mul(binormal,Math.sin(angle)));
        return [...add(p,mul(n,r)),...n,...color,phase+i/path.length];
      });
    });
    for (let i=0;i<rings.length-1;i++) for(let j=0;j<sides;j++) {
      const k=(j+1)%sides;
      mesh.push(...rings[i][j],...rings[i+1][j],...rings[i][k],
        ...rings[i][k],...rings[i+1][j],...rings[i+1][k]);
    }
    for (let i=1;i<path.length;i++) if(random()>.5) point(sparks,path[i],mix(color,pearl,.65),.012+random()*.018,random()*30);
  };
  const branch = (start,direction,length,radius,depth,isRoot=false) => {
    const phase=random()*Math.PI*2;
    const side=unit(cross(direction,[0,0,1]));
    const path=[];
    const steps=compact?6:8;
    for(let j=0;j<=steps;j++) {
      const u=j/steps;
      let p=add(start,mul(direction,length*u));
      p=add(p,mul(side,Math.sin(u*Math.PI)*length*.14*Math.sin(phase)));
      p[1]+=(isRoot?-.08:.17)*length*u*u;
      p[2]+=Math.sin(u*Math.PI)*length*.1*Math.cos(phase);
      path.push(p);
    }
    const tint=isRoot?mix(gold,pearl,.32):mix(gold,random()>.25?pearl:rose,Math.max(.12,1-depth*.22));
    tube(path,radius,tint,phase);
    // Capillary filaments surround each living branch, like nerves, mycelium
    // and the large-scale cosmic web. Their light has no hard surface.
    if(depth>1) for(let strand=0;strand<(compact?2:5);strand++) {
      let previous=null;
      const angle=phase+strand*2.399963;
      for(let j=0;j<=20;j++) {
        const u=j/20,index=u*(path.length-1),lo=Math.floor(index);
        const center=mix(path[lo],path[Math.min(lo+1,path.length-1)],index-lo);
        const spread=radius*(1.3+Math.sin(u*Math.PI)*1.8);
        const p=add(center,[Math.cos(angle+u*4)*spread,Math.sin(u*6+angle)*spread*.45,Math.sin(angle+u*4)*spread]);
        if(previous)filaments.push(...previous,...mix(tint,pearl,.7),phase,...p,...mix(tint,pearl,.7),phase+u);
        previous=p;
      }
    }
    const end=path[path.length-1];
    if(depth<=0) {
      const n=compact?3:5;
      for(let j=0;j<n;j++) {
        const p=add(end,[(random()-.5)*.1,(random()-.5)*.12,(random()-.5)*.1]);
        point(buds,p,mix(tint,[.9,.96,.92],.4),(.012+Math.pow(random(),3)*.066)*(isRoot?.65:1),random()*12);
      }
      return;
    }
    const count=depth>1&&!compact?3:2;
    for(let j=0;j<count;j++) {
      const theta=phase+j*Math.PI*2/count+(random()-.5)*.55;
      const radial=[Math.cos(theta),isRoot?-.35:.45,Math.sin(theta)];
      const next=unit(add(mul(direction,.85),mul(radial,.62)));
      branch(end,next,length*(.57+random()*.11),radius*.55,depth-1,isRoot);
    }
  };
  // We inhabit a small part of the tree. Each continuous braid passes beyond
  // the camera's view in both directions; there is no visible root or crown.
  const axes=[{x:1.5,z:0,phase:0},{x:-5.5,z:-7,phase:2.3},{x:7,z:-13,phase:4.6}];
  const axisPoint=(axis,y)=>[axis.x+Math.sin(y*.22+axis.phase)*.85+y*.13,
    y,axis.z+Math.cos(y*.17+axis.phase)*.7];
  for(let layer=0;layer<axes.length;layer++) {
    const axis=axes[layer],strands=layer===0?(compact?9:15):(compact?4:7);
    for(let strand=0;strand<strands;strand++) {
      const path=[],angle=strand/strands*Math.PI*2;
      for(let j=0;j<=100;j++) {
        const y=-20+j*.4,center=axisPoint(axis,y);
        const radius=.20+.055*Math.sin(y*.7+axis.phase);
        path.push(add(center,[Math.cos(angle+y*.9)*radius,0,Math.sin(angle+y*.9)*radius]));
      }
      tube(path,(layer===0?.044:.025)+random()*.026,mix(gold,pearl,.18+layer*.23),strand*.7);
    }
    const limbs=layer===0?(compact?20:26):(compact?8:14);
    for(let i=0;i<limbs;i++) {
      const span=layer===0?13:24;
      const y=-span/2+i/(limbs-1)*span,theta=i*2.399963+axis.phase;
      const direction=unit([Math.cos(theta),Math.sin(theta*1.7)*.8,Math.sin(theta)*.6]);
      branch(axisPoint(axis,y),direction,(layer===0?1.8:2.1)+random()*.7,
        (layer===0?.065:.045)+random()*.025,layer===0?4:2,direction[1]<0);
    }
  }
  // Long boughs weave between the braids and continue out of frame. Smaller
  // structures repeat along them, so a pearl is a world rather than an end.
  for(let i=0;i<(compact?7:12);i++) {
    const y=-10+i*1.8,from=axisPoint(axes[0],y);
    const target=axisPoint(axes[i%2+1],y+(i%2?5:-5));
    const path=[];
    for(let j=0;j<=36;j++) {
      const u=j/36,p=mix(from,target,u);
      p[1]+=Math.sin(u*Math.PI)*1.4;p[2]+=Math.sin(u*Math.PI)*1.8;
      path.push(p);
    }
    tube(path,.06,mix(gold,pearl,.45),i);
    for(let j=8;j<30;j+=7)branch(path[j],unit([Math.sin(i+j),.5,Math.cos(i-j)]),
      .7+random()*.5,.023,compact?1:2);
  }
  // Vast and microscopic structures share the same branching visual language.
  const starCount=compact?2700:5700;
  for(let i=0;i<starCount;i++) {
    const r=1.8+Math.pow(random(),.6)*15;
    const theta=r*.83+random()*.8+(i%3)*Math.PI*2/3;
    const p=[Math.cos(theta)*r,(random()-.5)*9+Math.sin(theta)*r*.35,Math.sin(theta)*r*.65-5.4];
    const c=mix([.18,.38,.48],[.84,.64,.41],random());
    point(dust,p,c,.004+random()*.017,random()*30);
  }
  for(let i=0;i<(compact?700:1500);i++) point(dust,
    [(random()-.5)*29,(random()-.5)*17,(random()-.5)*17-5],
    mix([.3,.6,.68],[.91,.79,.59],random()),.008+random()*.025,random()*40);

  const resources = [];
  const own = resource => {resources.push(resource);return resource;};
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#02070e');
  scene.fog = new THREE.FogExp2('#071722', .035);
  const camera = new THREE.PerspectiveCamera(48, 1, .1, 80);
  const clock = {value:17};
  const life = new THREE.Group();scene.add(life);
  const dataGeometry = (data,stride,layout) => {
    const geometry=own(new THREE.BufferGeometry());
    const interleaved=new THREE.InterleavedBuffer(new Float32Array(data),stride);
    for(const [name,size,offset] of layout)geometry.setAttribute(name,new THREE.InterleavedBufferAttribute(interleaved,size,offset));
    geometry.computeBoundingSphere();return geometry;
  };
  const treeGeometry=dataGeometry(mesh,10,[['position',3,0],['normal',3,3],['color',3,6]]);
  const branchMaterial=own(new THREE.MeshStandardMaterial({vertexColors:true,metalness:.42,roughness:.34,
    emissive:'#102b36',emissiveIntensity:.4}));
  branchMaterial.onBeforeCompile = shader => {
    shader.uniforms.lifeTime=clock;
    shader.vertexShader='varying vec3 vLifePosition;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',
      '#include <begin_vertex>\nvLifePosition=position;');
    shader.fragmentShader='uniform float lifeTime; varying vec3 vLifePosition;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <emissivemap_fragment>', `
      #include <emissivemap_fragment>
      float pulse=pow(.5+.5*sin(vLifePosition.y*2.8-lifeTime*.42),18.);
      totalEmissiveRadiance+=mix(vec3(.12,.42,.52),vec3(.8,.52,.21),pulse)*(.18+pulse*.7);
    `);
  };
  const tree = new THREE.Mesh(treeGeometry,branchMaterial);life.add(tree);
  const lineGeometry=dataGeometry(filaments,7,[['position',3,0],['color',3,3]]);
  const lineMaterial=own(new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.2,
    blending:THREE.AdditiveBlending,depthWrite:false}));
  life.add(new THREE.LineSegments(lineGeometry,lineMaterial));
  const pearlMaterial=own(new THREE.MeshPhysicalMaterial({color:'#d4f3f5',metalness:.13,roughness:.16,
    transmission:.25,thickness:.18,ior:1.35,iridescence:.85,iridescenceIOR:1.4,
    clearcoat:1,clearcoatRoughness:.12,emissive:'#184552',emissiveIntensity:.23}));
  const pearls=new THREE.InstancedMesh(own(new THREE.SphereGeometry(1,compact?7:10,compact?5:7)),pearlMaterial,buds.length/8);
  const dummy=new THREE.Object3D(),color=new THREE.Color();
  for(let i=0;i<buds.length;i+=8){
    dummy.position.fromArray(buds,i);dummy.scale.setScalar(buds[i+6]);dummy.updateMatrix();
    pearls.setMatrixAt(i/8,dummy.matrix);pearls.setColorAt(i/8,color.setRGB(buds[i+3],buds[i+4],buds[i+5]));
  }
  pearls.instanceMatrix.needsUpdate=true;pearls.instanceColor.needsUpdate=true;life.add(pearls);
  const particleMaterial=own(new THREE.ShaderMaterial({
    uniforms:{lifeTime:clock,pixelScale:{value:500}},vertexColors:true,transparent:true,
    blending:THREE.AdditiveBlending,depthWrite:false,
    vertexShader:`
      attribute float size,phase;varying vec3 vColor;varying float vPhase;
      uniform float lifeTime,pixelScale;
      void main(){vec3 p=position;p.x+=sin(lifeTime*.085+phase)*.018;p.y+=cos(lifeTime*.07+phase)*.018;
        vec4 mv=modelViewMatrix*vec4(p,1.);vColor=color;vPhase=phase;
        gl_Position=projectionMatrix*mv;gl_PointSize=clamp(size*pixelScale/max(.1,-mv.z),1.,48.);}
    `,
    fragmentShader:`
      uniform float lifeTime;varying vec3 vColor;varying float vPhase;
      void main(){vec2 p=gl_PointCoord*2.-1.;float r=dot(p,p);if(r>1.)discard;
        float alpha=exp(-r*5.)*(.65+.35*sin(lifeTime*.35+vPhase));
        gl_FragColor=vec4(vColor*(.7+pow(1.-r,8.)),alpha*.7);}
    `
  }));
  const pointGeometry = data => dataGeometry(data,8,[['position',3,0],['color',3,3],['size',1,6],['phase',1,7]]);
  const stars=new THREE.Points(pointGeometry(dust),particleMaterial);scene.add(stars);
  life.add(new THREE.Points(pointGeometry(sparks),particleMaterial));
  // A distant, luminous cloud field makes the same branches read at cosmic scale.
  const nebulaMaterial=own(new THREE.ShaderMaterial({depthTest:false,depthWrite:false,
    uniforms:{lifeTime:clock,aspect:{value:1},offset:{value:.3}},
    vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,1.,1.);}',
    fragmentShader:`
      precision highp float;varying vec2 vUv;uniform float lifeTime,aspect,offset;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
        return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+1.),f.x),f.y);}
      float fbm(vec2 p){float n=0.,a=.5;for(int i=0;i<5;i++){n+=a*noise(p);p=mat2(.8,.6,-.6,.8)*p*2.03+7.1;a*=.5;}return n;}
      void main(){vec2 p=(vUv-.5)*vec2(aspect,1.);p.x-=offset;
        vec2 drift=vec2(lifeTime*.0015,lifeTime*.0006);
        float n=fbm(p*3.2+drift),n2=fbm(p*5.+n*2.-drift);
        float haze=exp(-dot(p*vec2(.85,1.2),p*vec2(.85,1.2))*2.);
        float band=exp(-pow(p.y-p.x*.25+sin(p.x*2.)*.07,2.)*24.);
        vec3 c=vec3(.003,.008,.016)+vec3(.012,.044,.065)*haze;
        c+=mix(vec3(.018,.07,.11),vec3(.08,.035,.065),n2)*pow(n,2.)*band;
        float web=pow(max(0.,1.-abs(n2-.51)*12.),12.);c+=vec3(.03,.07,.095)*web*band*.4;
        gl_FragColor=vec4(c,1.);}
    `
  }));
  const nebula=new THREE.Mesh(own(new THREE.PlaneGeometry(2,2)),nebulaMaterial);
  nebula.frustumCulled=false;nebula.renderOrder=-1000;scene.add(nebula);
  scene.add(new THREE.HemisphereLight('#a9eaff','#3d1a17',.55));
  const key=new THREE.DirectionalLight('#fff0d6',1.4);key.position.set(-3,4,5);scene.add(key);
  const rim=new THREE.DirectionalLight('#83dcff',2.1);rim.position.set(3,2,-3);scene.add(rim);
  const heart=new THREE.PointLight('#ffc783',9,8,2);heart.position.set(1.2,-.4,2);scene.add(heart);
  const composer=new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene,camera));
  const bloom=new UnrealBloomPass(new THREE.Vector2(1,1),.42,.72,1.05);composer.addPass(bloom);
  composer.addPass(new OutputPass());
  // Procedural environment lighting stays local; no HDR image is downloaded.
  const environment=new RoomEnvironment();
  const pmrem=new THREE.PMREMGenerator(renderer);
  const environmentMap=pmrem.fromScene(environment,.04);
  scene.environment=environmentMap.texture;scene.environmentIntensity=.2;
  environment.dispose();pmrem.dispose();
  mesh.length=0;buds.length=0;dust.length=0;sparks.length=0;filaments.length=0;
  let stopped=reduced.matches,failed=false,frame=0,last=0;
  let pointerX=0,pointerY=0,lookX=0,lookY=0;
  const draw = () => {
    const mobile=camera.aspect<.85;
    const yaw=Math.sin(clock.value*.016)*.09+lookX*.045;
    const distance=(mobile?10.5:7.4)+Math.sin(clock.value*.018)*.3;
    const drift=Math.sin(clock.value*.012)*2.5;
    camera.position.set(Math.sin(yaw)*distance,drift+lookY*.25,Math.cos(yaw)*distance);
    camera.lookAt(mobile?.8:0,drift+.35,-1.5);
    life.position.set(mobile?-.45:1.1,0,0);
    life.rotation.z=.12+Math.sin(clock.value*.008)*.015;
    stars.rotation.y=clock.value*.0008;
    heart.intensity=2.8+Math.sin(clock.value*.25)*.5;
    composer.render();stage.classList.add('is-rendered');canvas.dataset.renderer='three.js';
  };
  const resize = () => {
    const {width,height}=stage.getBoundingClientRect();
    renderer.setPixelRatio(Math.min(devicePixelRatio||1,compact?1.25:1.6));renderer.setSize(width,height,false);
    composer.setPixelRatio(renderer.getPixelRatio());composer.setSize(width,height);
    camera.aspect=width/height;camera.updateProjectionMatrix();
    particleMaterial.uniforms.pixelScale.value=height*renderer.getPixelRatio()*1.4;
    nebulaMaterial.uniforms.aspect.value=camera.aspect;nebulaMaterial.uniforms.offset.value=camera.aspect<.85?0:.3;
    draw();
  };
  const animate = now => {
    frame=0;if(stopped||document.hidden||failed)return;
    if(now-last>=1000/30){clock.value+=Math.min((now-last)/1000,.06);last=now;
      lookX+=(pointerX-lookX)*.025;lookY+=(pointerY-lookY)*.025;draw();}
    frame=requestAnimationFrame(animate);
  };
  const updateMotion = () => {
    cancelAnimationFrame(frame);frame=0;last=performance.now();
    if(!stopped&&!document.hidden&&!failed)frame=requestAnimationFrame(animate);
  };
  reduced.addEventListener('change',()=>{stopped=reduced.matches;lookX=0;lookY=0;draw();updateMotion();});
  document.addEventListener('visibilitychange',updateMotion);
  stage.addEventListener('pointermove',event=>{if(stopped||compact)return;
    pointerX=event.clientX/innerWidth*2-1;pointerY=event.clientY/innerHeight*2-1;},{passive:true});
  stage.addEventListener('pointerleave',()=>{pointerX=0;pointerY=0;});
  new ResizeObserver(resize).observe(stage);
  canvas.addEventListener('webglcontextlost',()=>{failed=true;cancelAnimationFrame(frame);stage.classList.remove('is-rendered');});
  window.addEventListener('pagehide',event=>{cancelAnimationFrame(frame);if(event.persisted)return;for(const r of resources)r.dispose();
    environmentMap.dispose();composer.dispose();renderer.dispose();});
  window.addEventListener('pageshow',updateMotion);
  resize();updateMotion();
})();
