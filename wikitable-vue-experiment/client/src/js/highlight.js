const HighlightText = {
  // 高亮选中的文字（支持跨节点）
  highlightSelection(highlightColor = 'yellow') {
    const selection = window.getSelection();
    if (!selection.isCollapsed) {
      const range = selection.getRangeAt(0);
      const startContainer = range.startContainer;
      const endContainer = range.endContainer;

      // 遍历选区中的所有文本节点
      const textNodes = [];
      let node = startContainer;

      while (node) {
        if (node.nodeType === Node.TEXT_NODE) {
          textNodes.push(node);
        }

        // 如果当前节点是结束节点，停止遍历
        if (node === endContainer) break;

        // 移动到下一个节点
        node = this.getNextNode(node);
      }

      // 对每个文本节点进行高亮处理
      textNodes.forEach((textNode) => {
        const span = document.createElement('span');
        span.style.backgroundColor = highlightColor; // 设置高亮样式
        const parent = textNode.parentNode;
        parent.replaceChild(span, textNode);
        span.appendChild(textNode);
      });

      selection.removeAllRanges(); // 清除选区
    }
  },

  // 获取下一个节点
  getNextNode(node) {
    if (node.firstChild) return node.firstChild;
    while (node) {
      if (node.nextSibling) return node.nextSibling;
      node = node.parentNode;
    }
    return null;
  }
};

export default HighlightText;
