function createDoubleRafScheduler({
  nextTick,
  requestFrame,
  cancelFrame,
  task,
} = {}) {
  const runNextTick = typeof nextTick === "function" ? nextTick : callback => callback();
  const request = typeof requestFrame === "function"
    ? requestFrame
    : callback => setTimeout(callback, 0);
  const cancelRequest = typeof cancelFrame === "function"
    ? cancelFrame
    : id => clearTimeout(id);
  const runTask = typeof task === "function" ? task : () => {};
  let token = 0;
  let firstFrameId = null;
  let secondFrameId = null;
  let latestValue;

  const clearFrames = () => {
    if (firstFrameId !== null) cancelRequest(firstFrameId);
    if (secondFrameId !== null) cancelRequest(secondFrameId);
    firstFrameId = null;
    secondFrameId = null;
  };

  const cancel = () => {
    token += 1;
    clearFrames();
  };

  const schedule = value => {
    latestValue = value;
    const scheduledToken = ++token;
    clearFrames();
    runNextTick(() => {
      if (scheduledToken !== token) return;
      firstFrameId = request(() => {
        firstFrameId = null;
        if (scheduledToken !== token) return;
        secondFrameId = request(() => {
          secondFrameId = null;
          if (scheduledToken !== token) return;
          runTask(latestValue);
        });
      });
    });
  };

  return { schedule, cancel };
}

function createChartRenderController({
  nextTick,
  requestFrame,
  cancelFrame,
  eventTarget,
  getElement,
  isEmpty,
  createChart,
  buildOption,
  reset,
} = {}) {
  let chart = null;
  let chartElement = null;
  let mounted = false;
  let destroyed = false;

  const disposeChart = () => {
    chart?.dispose?.();
    chart = null;
    chartElement = null;
  };

  const scheduler = createDoubleRafScheduler({
    nextTick,
    requestFrame,
    cancelFrame,
    task: request => {
      if (destroyed) return;
      if (request?.reset) reset?.();
      const element = getElement?.();
      if (isEmpty?.() || !element) {
        disposeChart();
        return;
      }

      if (chart && chartElement !== element) disposeChart();

      const result = buildOption?.() || {};
      const option = Object.prototype.hasOwnProperty.call(result, "option")
        ? result.option
        : result;
      if (!chart) {
        chart = createChart?.(element) || null;
        chartElement = chart ? element : null;
      } else {
        chart.resize?.();
      }
      chart?.setOption?.(option, true);

      if (result.layoutChanged) scheduler.schedule();
    },
  });

  const schedule = request => {
    if (!destroyed) scheduler.schedule(request);
  };
  const handleResize = () => schedule();

  const mount = () => {
    if (mounted || destroyed) return;
    mounted = true;
    eventTarget?.addEventListener?.("resize", handleResize);
    schedule();
  };

  const destroy = () => {
    if (destroyed) return;
    destroyed = true;
    scheduler.cancel();
    if (mounted) eventTarget?.removeEventListener?.("resize", handleResize);
    mounted = false;
    disposeChart();
  };

  return { mount, schedule, destroy };
}

module.exports = {
  createChartRenderController,
  createDoubleRafScheduler,
};
