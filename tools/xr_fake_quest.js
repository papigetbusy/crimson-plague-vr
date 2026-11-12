/* A fake Meta Quest for headless Chrome: navigator.xr, an immersive-vr session, a head and two Touch controllers
   (xr-standard gamepads with haptics) that a test script moves through window.__fx. Enough of WebXR for three.js r128. */
(() => {
  const btn = () => Array.from({ length: 7 }, () => ({ pressed: false, touched: false, value: 0 }));
  const S = window.__fx = {
    head: { p: [0, 0, 0], q: [0, 0, 0, 1] },
    hands: {
      left: { p: [-0.18, -0.45, -0.3], q: [0, 0, 0, 1], v: [0, 0, 0, 0, 0, 0, 0], ax: [0, 0, 0, 0] },
      right: { p: [0.18, -0.45, -0.3], q: [0, 0, 0, 1], v: [0, 0, 0, 0, 0, 0, 0], ax: [0, 0, 0, 0] }
    },
    pulses: [], frames: 0, session: null, errors: []
  };
  window.addEventListener('error', (e) => S.errors.push(String(e.message)));
  function mat(p, q) {
    const [x, y, z, w] = q, x2 = x + x, y2 = y + y, z2 = z + z, xx = x * x2, xy = x * y2, xz = x * z2, yy = y * y2, yz = y * z2, zz = z * z2, wx = w * x2, wy = w * y2, wz = w * z2;
    return new Float32Array([1 - (yy + zz), xy + wz, xz - wy, 0, xy - wz, 1 - (xx + zz), yz + wx, 0, xz + wy, yz - wx, 1 - (xx + yy), 0, p[0], p[1], p[2], 1]);
  }
  function rot(v, q) {   // rotate vector v by quaternion q
    const [x, y, z, w] = q, [vx, vy, vz] = v;
    const ix = w * vx + y * vz - z * vy, iy = w * vy + z * vx - x * vz, iz = w * vz + x * vy - y * vx, iw = -x * vx - y * vy - z * vz;
    return [ix * w + iw * -x + iy * -z - iz * -y, iy * w + iw * -y + iz * -x - ix * -z, iz * w + iw * -z + ix * -y - iy * -x];
  }
  class XRRigidTransform { constructor(p, q) { p = p || [0, 0, 0]; q = q || [0, 0, 0, 1]; this.matrix = mat(p, q); this.position = { x: p[0], y: p[1], z: p[2], w: 1 }; this.orientation = { x: q[0], y: q[1], z: q[2], w: q[3] }; } }
  const f = 1 / Math.tan(Math.PI / 4), n = 0.05, fa = 500;   // 90 degree square eyes
  const PROJ = new Float32Array([f, 0, 0, 0, 0, f, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, (2 * fa * n) / (n - fa), 0]);
  class Space { constructor(hand) { this.hand = hand; } }
  class XRWebGLLayer {
    constructor(session, gl) { this._gl = gl; this.framebuffer = null; this.framebufferWidth = gl.drawingBufferWidth; this.framebufferHeight = gl.drawingBufferHeight; this.antialias = true; this.ignoreDepthValues = false; }
    getViewport(view) { const w = this._gl.drawingBufferWidth, h = this._gl.drawingBufferHeight; return view.eye === 'left' ? { x: 0, y: 0, width: w / 2, height: h } : { x: w / 2, y: 0, width: w / 2, height: h }; }
  }
  class Frame {
    constructor(s) { this.session = s; }
    getViewerPose() {
      const h = S.head;
      const views = ['left', 'right'].map((eye) => { const o = rot([eye === 'left' ? -0.032 : 0.032, 0, 0], h.q); return { eye, transform: new XRRigidTransform([h.p[0] + o[0], h.p[1] + o[1], h.p[2] + o[2]], h.q), projectionMatrix: PROJ }; });
      return { transform: new XRRigidTransform(h.p, h.q), views, emulatedPosition: false };
    }
    getPose(space) { const hd = space && S.hands[space.hand]; return hd ? { transform: new XRRigidTransform(hd.p, hd.q), emulatedPosition: false } : null; }
  }
  function makeSource(hand) {
    const gp = { id: 'oculus-touch-v3 ' + hand, index: -1, connected: true, mapping: 'xr-standard', axes: [0, 0, 0, 0], buttons: btn(), timestamp: 0,
      hapticActuators: [{ type: 'vibration', pulse: (s, ms) => { S.pulses.push({ hand, s, ms, f: S.frames }); return Promise.resolve(true); } }] };
    return { handedness: hand, targetRayMode: 'tracked-pointer', targetRaySpace: new Space(hand), gripSpace: new Space(hand), gamepad: gp, profiles: ['meta-quest-touch-plus', 'oculus-touch-v3'] };
  }
  class Session extends EventTarget {
    constructor() { super(); this.renderState = { baseLayer: null, depthNear: 0.1, depthFar: 1000 }; this.inputSources = []; this.visibilityState = 'visible'; this._cbs = new Map(); this._id = 0; this._ended = false; this.environmentBlendMode = 'opaque'; }
    updateRenderState(s) { Object.assign(this.renderState, s); }
    async requestReferenceSpace() { return new Space(null); }
    requestAnimationFrame(cb) { const id = ++this._id; this._cbs.set(id, cb); if (!this._raf) this._raf = window.requestAnimationFrame((t) => this._tick(t)); return id; }
    cancelAnimationFrame(id) { this._cbs.delete(id); }
    _tick(t) {
      this._raf = 0; if (this._ended) return;
      S.frames++;
      for (const src of this.inputSources) { const hd = S.hands[src.handedness], g = src.gamepad; for (let i = 0; i < 7; i++) { const v = hd.v[i] || 0; g.buttons[i].value = v; g.buttons[i].pressed = v > 0.5; g.buttons[i].touched = v > 0; } for (let i = 0; i < 4; i++) g.axes[i] = hd.ax[i] || 0; g.timestamp = t; }
      const cbs = [...this._cbs.values()]; this._cbs.clear(); const fr = new Frame(this);
      for (const cb of cbs) { try { cb(t, fr); } catch (e) { S.errors.push('frame: ' + (e && e.stack || e)); } }
    }
    async end() { if (this._ended) return; this._ended = true; this.dispatchEvent(new Event('end')); }
  }
  const xr = {
    isSessionSupported: async (m) => m === 'immersive-vr',
    requestSession: async () => {
      const s = new Session(); S.session = s;
      setTimeout(() => { s.inputSources = [makeSource('left'), makeSource('right')]; const e = new Event('inputsourceschange'); e.added = s.inputSources.slice(); e.removed = []; s.dispatchEvent(e); }, 200);
      return s;
    },
    addEventListener() {}, removeEventListener() {}
  };
  Object.defineProperty(navigator, 'xr', { value: xr, configurable: true });
  window.XRWebGLLayer = XRWebGLLayer; window.XRRigidTransform = XRRigidTransform;
  for (const C of [window.WebGLRenderingContext, window.WebGL2RenderingContext]) if (C) C.prototype.makeXRCompatible = function () { return Promise.resolve(); };
})();
