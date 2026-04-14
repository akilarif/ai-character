import { startApp } from "./src/app.js";
import { applyPixiCompat } from "./src/pixi-compat.js";

applyPixiCompat();
void startApp();
