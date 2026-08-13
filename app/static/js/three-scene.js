/**
 * Three.js Interactive 3D Background Engine
 * Creates a subtle particle constellation with floating geometric nodes
 */
function initThreeScene() {
  const canvas = document.getElementById('webgl-canvas');
  if (!canvas || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 80;

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Particle System
  const particleCount = 280;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);

  const colorPalette = [
    new THREE.Color('#6366f1'), // Indigo
    new THREE.Color('#38bdf8'), // Cyan
    new THREE.Color('#10b981'), // Emerald
    new THREE.Color('#818cf8')  // Soft Purple
  ];

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 160;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 160;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 120;

    const chosenColor = colorPalette[Math.floor(Math.random() * colorPalette.length)];
    colors[i * 3] = chosenColor.r;
    colors[i * 3 + 1] = chosenColor.g;
    colors[i * 3 + 2] = chosenColor.b;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  // Circular particle texture generator
  const canvasTexture = document.createElement('canvas');
  canvasTexture.width = 64;
  canvasTexture.height = 64;
  const ctx = canvasTexture.getContext('2d');
  const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
  grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.8)');
  grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 64, 64);
  const pTexture = new THREE.CanvasTexture(canvasTexture);

  const material = new THREE.PointsMaterial({
    size: 2.2,
    vertexColors: true,
    map: pTexture,
    transparent: true,
    opacity: 0.65,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  const particleSystem = new THREE.Points(geometry, material);
  scene.add(particleSystem);

  // Floating Wireframe Icosahedron
  const icoGeo = new THREE.IcosahedronGeometry(22, 1);
  const icoMat = new THREE.MeshBasicMaterial({
    color: 0x6366f1,
    wireframe: true,
    transparent: true,
    opacity: 0.12
  });
  const icoMesh = new THREE.Mesh(icoGeo, icoMat);
  icoMesh.position.set(40, -10, -20);
  scene.add(icoMesh);

  // Floating Torus
  const torusGeo = new THREE.TorusGeometry(16, 1.2, 16, 50);
  const torusMat = new THREE.MeshBasicMaterial({
    color: 0x0ea5e9,
    wireframe: true,
    transparent: true,
    opacity: 0.08
  });
  const torusMesh = new THREE.Mesh(torusGeo, torusMat);
  torusMesh.position.set(-45, 15, -30);
  scene.add(torusMesh);

  // Mouse Interaction
  let mouseX = 0;
  let mouseY = 0;
  let targetX = 0;
  let targetY = 0;

  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX - window.innerWidth / 2) * 0.04;
    mouseY = (e.clientY - window.innerHeight / 2) * 0.04;
  });

  // Resize Handler
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // Animation Loop
  let clock = new THREE.Clock();
  function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    targetX += (mouseX - targetX) * 0.05;
    targetY += (mouseY - targetY) * 0.05;

    particleSystem.rotation.y = elapsedTime * 0.03 + targetX * 0.02;
    particleSystem.rotation.x = elapsedTime * 0.02 + targetY * 0.02;

    icoMesh.rotation.x = elapsedTime * 0.05;
    icoMesh.rotation.y = elapsedTime * 0.08;
    icoMesh.position.y = -10 + Math.sin(elapsedTime * 0.5) * 4;

    torusMesh.rotation.x = elapsedTime * 0.04;
    torusMesh.rotation.z = elapsedTime * 0.06;
    torusMesh.position.y = 15 + Math.cos(elapsedTime * 0.6) * 3;

    camera.position.x = targetX * 0.3;
    camera.position.y = -targetY * 0.3;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
  }

  animate();
}

document.addEventListener('DOMContentLoaded', initThreeScene);
