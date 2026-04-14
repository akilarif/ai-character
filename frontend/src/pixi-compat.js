// PixiJS v8 moved settings. This maps them back so the plugin doesn't crash.
export function applyPixiCompat() {
  window.PIXI.Assets = window.PIXI.Assets || {};
  window.PIXI.settings = window.PIXI.settings || {};
  window.PIXI.sound = window.PIXI.sound || {};
  window.PIXI.Sound = window.PIXI.sound || {};
  window.PIXI.utils = window.PIXI.utils || {};

  if (PIXI.Assets && !PIXI.Assets.from) {
    PIXI.Assets.from = PIXI.Assets.load;
  }
  if (PIXI.sound && !PIXI.sound.from) {
    PIXI.sound.from = PIXI.sound.add;
  }
}
