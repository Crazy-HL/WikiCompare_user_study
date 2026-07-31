const assert = require("assert");
const {
  createChartRenderController,
  createDoubleRafScheduler,
} = require("../src/js/chartRenderScheduler");

function createRuntime() {
  let nextFrameId = 1;
  const frames = new Map();
  const listeners = new Map();
  return {
    nextTick(callback) { callback(); },
    requestFrame(callback) {
      const id = nextFrameId++;
      frames.set(id, callback);
      return id;
    },
    cancelFrame(id) { frames.delete(id); },
    flushFrame() {
      const pending = [...frames.entries()];
      frames.clear();
      pending.forEach(([, callback]) => callback());
    },
    flushDoubleFrame() {
      this.flushFrame();
      this.flushFrame();
    },
    pendingFrames() { return frames.size; },
    eventTarget: {
      addEventListener(name, callback) { listeners.set(name, callback); },
      removeEventListener(name, callback) {
        if (listeners.get(name) === callback) listeners.delete(name);
      },
    },
    emit(name) { listeners.get(name)?.(); },
    hasListener(name) { return listeners.has(name); },
  };
}

{
  const runtime = createRuntime();
  const renders = [];
  const scheduler = createDoubleRafScheduler({
    nextTick: runtime.nextTick,
    requestFrame: runtime.requestFrame,
    cancelFrame: runtime.cancelFrame,
    task: value => renders.push(value),
  });
  scheduler.schedule("first");
  scheduler.schedule("last");
  runtime.flushDoubleFrame();
  assert.deepStrictEqual(renders, ["last"], "rapid schedules must render only the latest task");

  scheduler.schedule("cancelled");
  scheduler.cancel();
  runtime.flushDoubleFrame();
  assert.deepStrictEqual(renders, ["last"]);
  assert.strictEqual(runtime.pendingFrames(), 0);
}

{
  const runtime = createRuntime();
  const element = { clientHeight: 500 };
  let empty = false;
  let mode = "auto";
  let propsVersion = 1;
  let controlsVisible = false;
  let initCount = 0;
  let disposeCount = 0;
  const resizeHeights = [];
  const setOptions = [];
  const resetModes = [];

  const controller = createChartRenderController({
    nextTick: runtime.nextTick,
    requestFrame: runtime.requestFrame,
    cancelFrame: runtime.cancelFrame,
    eventTarget: runtime.eventTarget,
    getElement: () => element,
    isEmpty: () => empty,
    createChart: () => {
      initCount += 1;
      return {
        resize: () => resizeHeights.push(element.clientHeight),
        setOption: option => setOptions.push(option),
        dispose: () => { disposeCount += 1; },
      };
    },
    buildOption: () => {
      const nextControlsVisible = mode === "auto";
      const layoutChanged = controlsVisible !== nextControlsVisible;
      controlsVisible = nextControlsVisible;
      return {
        option: { height: element.clientHeight, mode, propsVersion },
        layoutKey: controlsVisible,
        layoutChanged,
      };
    },
    reset: () => {
      mode = "auto";
      resetModes.push(mode);
    },
  });

  controller.mount();
  assert(runtime.hasListener("resize"));
  runtime.flushDoubleFrame();
  assert.strictEqual(setOptions.length, 1);
  assert.strictEqual(runtime.pendingFrames(), 1, "controls appearing must schedule a second layout pass");
  runtime.flushDoubleFrame();
  assert.strictEqual(setOptions.length, 2);
  assert.strictEqual(runtime.pendingFrames(), 0);

  element.clientHeight = 620;
  runtime.emit("resize");
  runtime.flushDoubleFrame();
  assert.strictEqual(setOptions.at(-1).height, 620, "resize must rebuild using the new height");
  assert.strictEqual(resizeHeights.at(-1), 620);

  mode = "linear";
  controller.schedule();
  mode = "index";
  controller.schedule();
  runtime.flushDoubleFrame();
  assert.strictEqual(setOptions.at(-1).mode, "index", "mode changes must set the final option only");
  runtime.flushDoubleFrame();

  mode = "linear";
  propsVersion = 2;
  controller.schedule({ reset: true });
  runtime.flushDoubleFrame();
  assert.strictEqual(resetModes.at(-1), "auto", "prop changes must reset mode to auto");
  assert.deepStrictEqual(setOptions.at(-1), { height: 620, mode: "auto", propsVersion: 2 });
  runtime.flushDoubleFrame();

  empty = true;
  controller.schedule();
  runtime.flushDoubleFrame();
  assert.strictEqual(disposeCount, 1);
  empty = false;
  controller.schedule();
  runtime.flushDoubleFrame();
  assert.strictEqual(initCount, 2, "empty to populated must re-initialize a disposed chart");
  empty = true;
  controller.schedule();
  runtime.flushDoubleFrame();
  assert.strictEqual(disposeCount, 2, "populated to empty must dispose again");

  empty = false;
  controller.schedule();
  controller.destroy();
  runtime.flushDoubleFrame();
  assert.strictEqual(runtime.pendingFrames(), 0, "unmount must cancel pending RAF work");
  assert.strictEqual(runtime.hasListener("resize"), false, "unmount must remove resize listener");
  assert.strictEqual(disposeCount, 2, "destroy must not double-dispose after an empty render");
}


{
  const runtime = createRuntime();
  const elementA = { id: "A", clientHeight: 500 };
  const elementB = { id: "B", clientHeight: 620 };
  let currentElement = elementA;
  let empty = false;
  const createdFor = [];
  const disposedFor = [];
  const setOptions = [];

  const controller = createChartRenderController({
    nextTick: runtime.nextTick,
    requestFrame: runtime.requestFrame,
    cancelFrame: runtime.cancelFrame,
    eventTarget: runtime.eventTarget,
    getElement: () => currentElement,
    isEmpty: () => empty,
    createChart: element => {
      createdFor.push(element.id);
      return {
        resize: () => {},
        setOption: option => setOptions.push({ element: element.id, option }),
        dispose: () => disposedFor.push(element.id),
      };
    },
    buildOption: () => ({ option: { element: currentElement.id } }),
  });

  controller.mount();
  runtime.flushDoubleFrame();
  assert.deepStrictEqual(createdFor, ["A"]);
  assert.deepStrictEqual(setOptions, [{ element: "A", option: { element: "A" } }]);

  empty = true;
  controller.schedule();
  empty = false;
  currentElement = elementB;
  controller.schedule();
  runtime.flushDoubleFrame();

  assert.deepStrictEqual(disposedFor, ["A"], "changing chart elements must dispose the chart bound to A once");
  assert.deepStrictEqual(createdFor, ["A", "B"], "the restored chart must initialize against element B");
  assert.deepStrictEqual(
    setOptions,
    [
      { element: "A", option: { element: "A" } },
      { element: "B", option: { element: "B" } },
    ],
    "the restored option must be written only to the chart bound to B"
  );

  controller.destroy();
  assert.deepStrictEqual(disposedFor, ["A", "B"], "destroy must dispose B once without re-disposing A");
}

console.log("chartRenderScheduler executable tests passed");
