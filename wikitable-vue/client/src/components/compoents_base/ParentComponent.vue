<template>
	<div :class="['div0', selectContentClass]" :id="divId" ref="divRef">
		<h1>{{ props.pageTitle }}</h1>

		<LoadingSpinner v-if="loading" />

		<ErrorDisplay
			v-else-if="error"
			:message="error"
			@retry="fetchWikipediaContent" />

		<WikipediaContent v-else :content="pageHtml" @select="handleSelection" />

		<TextPopup
			:visible="showPopup[divId]"
			:content="selectedText[divId]"
			:containerClass="
				divId === 'div1' ? 'chart-container1' : 'chart-container2'
			"
			:containerRef="divRef"
			@close="closePopup" />

		<ArticleOutline :content="pageHtml" :divId="divId" />
	</div>
</template>

<script>
	import { ref, onMounted, onUnmounted, nextTick } from "vue";
	import LoadingSpinner from "./LoadingSpinner.vue";
	import ErrorDisplay from "./ErrorDisplay.vue";
	import WikipediaContent from "./WikipediaContent.vue";
	import TextPopup from "./TextPopup.vue";
	import ArticleOutline from "./ArticleOutline.vue";
	import * as d3 from "d3";
	import bus from "@/js/eventBus.js";
	import { parseInfoboxForComparison } from "@/js/wikiInfoboxParser";

	export default {
		components: {
			LoadingSpinner,
			ErrorDisplay,
			WikipediaContent,
			TextPopup,
			ArticleOutline
		},
		props: {
			pageTitle: String,
			divId: String,
			selectContentClass: String,
			linkedOutline: Array,
			revision: String
		},
		setup(props) {
			const pageHtml = ref("");
			const loading = ref(true);
			const error = ref("");
			const selectedText = ref({});
			const showPopup = ref({});
			const divRef = ref(null);
			const MainTextContent = ref("");
			const revisionId = ref(props.revision || null);
			const highlightCache = ref(new Map());

			const fetchWikipediaContent = async () => {
				try {
					let apiUrl = `https://en.wikipedia.org/api/rest_v1/page/html/${encodeURIComponent(
						props.pageTitle
					)}`;
					if (revisionId.value) {
						apiUrl += `/${revisionId.value}`;
					}
					const response = await fetch(apiUrl);
					if (!response.ok) throw new Error("Failed to fetch data");

					const html = await response.text();
					MainTextContent.value = cleanWikipediaContent(html);
					const parser = new DOMParser();
					const doc = parser.parseFromString(html, "text/html");

					const infobox = doc.querySelector(".infobox, .sidebar, .toccolours");
					const comparisonData = parseInfoboxForComparison(infobox);

					const sidebar = doc.querySelector(".sidebar");
					if (sidebar) sidebar.remove();

					bus.emit(`${props.divId}_InfoboxData`, comparisonData);

					const headings = doc.querySelectorAll("h1, h2, h3, h4, h5, h6");
					headings.forEach((heading, index) => {
						const uniqueId = `heading-${index}-${props.divId}`;
						heading.id = uniqueId;
					});

					const tables = doc.querySelectorAll("table");
					tables.forEach(table => {
						table.classList.add("custom-table");
					});

					const styles = Array.from(
						doc.querySelectorAll('link[rel="stylesheet"]')
					);
					styles.forEach(link => {
						if (!document.querySelector(`link[href="${link.href}"]`)) {
							const styleTag = document.createElement("link");
							styleTag.rel = "stylesheet";
							styleTag.href = link.href;
							document.head.appendChild(styleTag);
						}
					});

					const contentElement = doc.querySelector("body");
					if (!contentElement) throw new Error("Content not found");

					pageHtml.value = contentElement.innerHTML;
					highlightCache.value.clear();
					injectWikipediaStyles();

					bus.emit(`${props.divId}_FullContent`, {
						content: pageHtml.value,
						title: props.pageTitle
					});
				} catch (err) {
					error.value = "Error fetching Wikipedia content: " + err.message;
					console.error("获取维基百科内容失败:", err);
				} finally {
					loading.value = false;
				}
			};

			const cleanWikipediaContent = html => {
				const parser = new DOMParser();
				const doc = parser.parseFromString(html, "text/html");

				const selectorsToRemove = [
					".infobox",
					".sidebar",
					".toc",
					".reflist",
					".hatnote",
					".navbox",
					".mw-editsection",
					"table.ambox",
					".shortdescription",
					"img",
					"figure"
				];
				selectorsToRemove.forEach(selector => {
					doc.querySelectorAll(selector).forEach(el => el.remove());
				});
				const bodyContent =
					doc.querySelector("#bodyContent, #mw-content-text") || doc.body;
				let plainText = bodyContent.textContent || bodyContent.innerText;
				plainText = plainText
					.replace(/\s+/g, " ")
					.replace(/\[\d+\]/g, "")
					.trim();
				return plainText;
			};

			const injectWikipediaStyles = () => {
				const wikipediaStyles = [
					"https://en.wikipedia.org/w/load.php?modules=site.styles",
					"https://en.wikipedia.org/w/load.php?modules=ext.cite.styles",
					"https://en.wikipedia.org/w/load.php?modules=ext.scribunto.styles",
					"https://en.wikipedia.org/w/load.php?modules=skins.vector.styles"
				];
				wikipediaStyles.forEach(url => {
					if (!document.querySelector(`link[href="${url}"]`)) {
						const styleTag = document.createElement("link");
						styleTag.rel = "stylesheet";
						styleTag.href = url;
						document.head.appendChild(styleTag);
					}
				});
			};

			const handleHoverInfobox = ({ fieldKey, infoboxTitle }) => {
				if (props.pageTitle !== infoboxTitle) return;
				const infobox = divRef.value.querySelector(
					".infobox, .sidebar, .toccolours"
				);
				if (!infobox) return;
				clearInfoboxHighlights();
				const rows = infobox.querySelectorAll("tr");
				for (const row of rows) {
					const th = row.querySelector("th");
					if (th && th.textContent.trim() === fieldKey) {
						row.classList.add("infobox-highlight");
						break;
					}
				}
			};

			const handleUnhoverInfobox = () => {
				clearInfoboxHighlights();
				clearTextHighlights();
			};

			const handleSelection = content => {
				const isTable = /<table.*?>.*?<\/table>/s.test(content);
				const selection = window.getSelection();
				if (!selection || selection.rangeCount === 0) return;
				const range = selection.getRangeAt(0);
				const selectedNodes = range.cloneContents().childNodes;
				let sourceId = undefined;
				for (const node of selectedNodes) {
					if (
						node.nodeType === Node.ELEMENT_NODE &&
						/^h[1-6]$/i.test(node.tagName)
					) {
						sourceId = node.id;
						break;
					}
				}
				if (!sourceId) {
					let startElement = range.startContainer;
					while (startElement && !/^h[1-6]$/i.test(startElement.tagName)) {
						startElement = startElement.parentElement;
					}
					sourceId = startElement ? startElement.id : undefined;
				}
				if (!sourceId) {
					selectedText.value[props.divId] = content;
					bus.emit(`${props.divId}_Event`, { content });
					showPopup.value[props.divId] = true;
					nextTick(() => {
						updatePopupPosition();
					});
					return;
				}
				handleSelectionWithSourceId(content, sourceId, isTable);
			};

			const handleSelectionWithSourceId = (content, sourceId, isTable) => {
				selectedText.value[props.divId] = content;
				bus.emit(`${props.divId}_Event`, { content });
				showPopup.value[props.divId] = true;
				if (isTable) {
					const { linkedItem, chapterContent } = extractLinkedChapterContent(
						sourceId,
						props.divId
					);
					if (linkedItem && chapterContent) {
						const otherContainerId = props.divId === "div1" ? "div3" : "div1";
						const targetId =
							props.divId === "div1" ? linkedItem.rightId : linkedItem.leftId;
						const targetElement = document.getElementById(targetId);
						if (targetElement) {
							targetElement.scrollIntoView({ behavior: "smooth" });
						}
						bus.emit(`${otherContainerId}_Event`, { content: chapterContent });
						bus.emit(`${otherContainerId}Event`, {
							content: chapterContent,
							sourceId: sourceId
						});
					}
				}
				nextTick(() => {
					updatePopupPosition();
				});
			};

			const closePopup = () => {
				showPopup.value[props.divId] = false;
				selectedText.value[props.divId] = "";
				const container =
					props.divId === "div1" ? ".chart-container1" : ".chart-container2";
				d3.select(container).html("");
			};

			const updatePopupPosition = () => {
				if (showPopup.value[props.divId] && divRef.value) {
					const popup = divRef.value.querySelector(".text-popup");
					const overlay = divRef.value.querySelector(".overlay");
					if (popup && overlay) {
						const rect = divRef.value.getBoundingClientRect();
						const scrollTop = divRef.value.scrollTop;
						const scrollLeft = divRef.value.scrollLeft;
						overlay.style.top = `${scrollTop}px`;
						overlay.style.left = `${scrollLeft}px`;
						overlay.style.width = `${divRef.value.clientWidth}px`;
						overlay.style.height = `${divRef.value.clientHeight}px`;
						popup.style.top = `${rect.height / 2 + scrollTop}px`;
						popup.style.left = `${rect.width / 2 + scrollLeft}px`;
					}
				}
			};

			const extractLinkedChapterContent = (sourceId, sourceContainerId) => {
				if (!props.linkedOutline)
					return { linkedItem: null, chapterContent: "" };
				const linkedItem = props.linkedOutline.find(
					linked => linked.leftId === sourceId || linked.rightId === sourceId
				);
				if (!linkedItem) return { linkedItem: null, chapterContent: "" };
				const targetContainerId =
					sourceContainerId === "div1" ? "div3" : "div1";
				const targetId =
					sourceContainerId === "div1" ? linkedItem.rightId : linkedItem.leftId;
				const targetContainer = document.getElementById(targetContainerId);
				if (!targetContainer) return { linkedItem: null, chapterContent: "" };
				const targetElement = targetContainer.querySelector(`#${targetId}`);
				if (!targetElement) return { linkedItem: null, chapterContent: "" };
				let chapterContent = "";
				let currentNode = targetElement;
				while (currentNode) {
					if (
						currentNode !== targetElement &&
						currentNode.nodeType === Node.ELEMENT_NODE &&
						/^h[1-6]$/i.test(currentNode.tagName)
					)
						break;
					if (
						currentNode.nodeType === Node.ELEMENT_NODE ||
						currentNode.nodeType === Node.TEXT_NODE
					) {
						chapterContent += currentNode.outerHTML || currentNode.textContent;
					}
					currentNode = currentNode.nextSibling;
				}
				return { linkedItem, chapterContent };
			};

			const clearInfoboxHighlights = () => {
				const infobox = divRef.value.querySelector(
					".infobox, .sidebar, .toccolours"
				);
				if (infobox) {
					const highlightClasses = [
						"step-highlight-left",
						"step-highlight-right",
						"chain-highlight-left",
						"chain-highlight-right",
						"infobox-highlight"
					];
					highlightClasses.forEach(className => {
						infobox.querySelectorAll(`.${className}`).forEach(el => {
							el.classList.remove(className);
						});
					});
				}
			};

			const getSearchTermsForField = field => {
				const baseTerms = [field];
				const variants = {
					"GDP growth": [
						"GDP growth",
						"economic growth",
						"growth rate",
						"经济增长"
					],
					Population: ["Population", "population", "人口", "居民"],
					GDP: ["GDP", "gross domestic product", "国内生产总值"],
					"Export goods": ["Export", "export", "exports", "出口"],
					"Import goods": ["Import", "import", "imports", "进口"],
					"GDP by sector": [
						"GDP by sector",
						"sector",
						"industry",
						"产业",
						"行业"
					],
					"GDP per capita": ["GDP per capita", "per capita", "人均"],
					"Main industries": ["Main industries", "industries", "产业", "工业"],
					"Inflation (CPI)": [
						"Inflation",
						"CPI",
						"inflation",
						"通胀",
						"通货膨胀"
					],
					"Main export partners": [
						"export partners",
						"trading partners",
						"贸易伙伴"
					],
					"Labor force by occupation": [
						"Labor force",
						"workforce",
						"劳动力",
						"就业"
					],
					Unemployment: ["Unemployment", "unemployed", "失业"],
					"Gini coefficient": ["Gini", "Gini coefficient", "基尼系数"],
					"Population below poverty line": [
						"poverty",
						"poverty line",
						"贫困",
						"贫困线"
					]
				};
				return variants[field] ? [...baseTerms, ...variants[field]] : baseTerms;
			};

			// --- OPTIMIZATION & CACHING LOGIC ---

			const clearTextHighlights = () => {
				const contentElement = divRef.value;
				if (!contentElement) return;
				requestAnimationFrame(() => {
					const highlights = contentElement.querySelectorAll(
						".sentence-highlight"
					);
					highlights.forEach(highlight => {
						const parent = highlight.parentNode;
						if (parent) {
							while (highlight.firstChild) {
								parent.insertBefore(highlight.firstChild, highlight);
							}
							parent.removeChild(highlight);
						}
					});
					contentElement.normalize();
				});
			};

			// ---- NEW HELPER FUNCTION ----
			/**
			 * 智能提取一个元素内的文本节点和内容，会跳过维基百科的引用标记（sup.mw-ref）。
			 * @param {HTMLElement} element - 要提取内容的父元素。
			 * @returns {{textNodes: Text[], textContent: string}} - 包含有效文本节点数组和拼接后内容的对。
			 */
			const getTextNodesAndContent = element => {
				const textNodes = [];
				let textContent = "";
				const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
				let node;
				while ((node = walker.nextNode())) {
					// 检查当前文本节点的父元素是否是引用标记，如果是则跳过
					if (node.parentElement && node.parentElement.closest("sup.mw-ref")) {
						continue;
					}
					textNodes.push(node);
					textContent += node.nodeValue;
				}
				return { textNodes, textContent };
			};

			// ---- MODIFIED HELPER FUNCTION ----
			// createRangeForText 现在接收一个预先过滤好的 textNodes 数组
			const createRangeForText = (textNodes, fullText, start, length) => {
				let charCount = 0;
				let startNode, startOffset, endNode, endOffset;

				for (const currentNode of textNodes) {
					const nodeLength = currentNode.nodeValue.length;
					if (!startNode && charCount + nodeLength > start) {
						startNode = currentNode;
						startOffset = start - charCount;
					}
					if (startNode && charCount + nodeLength >= start + length) {
						endNode = currentNode;
						endOffset = start + length - charCount;
						break;
					}
					charCount += nodeLength;
				}

				if (startNode && endNode) {
					const range = document.createRange();
					range.setStart(startNode, startOffset);
					range.setEnd(endNode, endOffset);
					return range;
				}
				return null;
			};

			// ---- MODIFIED CORE FUNCTION ----
			// calculateAndCacheRangesForField 现在使用新的文本提取逻辑
			const calculateAndCacheRangesForField = field => {
				const contentElement = divRef.value;
				if (!contentElement) return [];

				const limit = 6;
				let foundCount = 0;
				const searchTerms = new Set(getSearchTermsForField(field));
				const newlyFoundRanges = [];
				const segmenter = new Intl.Segmenter(undefined, {
					granularity: "sentence"
				});

				const blockElements = contentElement.querySelectorAll(
					"p, li, dd, h1, h2, h3, h4, h5, h6, blockquote, caption, .toctext"
				);

				for (const block of blockElements) {
					if (foundCount >= limit) break;
					if (block.closest(".infobox, .sidebar, .toccolours")) continue;

					// 使用新的智能文本提取函数
					const { textNodes, textContent: cleanBlockText } =
						getTextNodesAndContent(block);
					if (!cleanBlockText) continue;

					const sentences = Array.from(segmenter.segment(cleanBlockText)).map(
						s => s.segment
					);

					for (const sentence of sentences) {
						if (
							Array.from(searchTerms).some(term =>
								sentence.toLowerCase().includes(term.toLowerCase())
							)
						) {
							const sentenceStartIndex = cleanBlockText.indexOf(sentence);
							if (sentenceStartIndex === -1) continue;

							// 将过滤后的 textNodes 传给 createRangeForText
							const range = createRangeForText(
								textNodes,
								cleanBlockText,
								sentenceStartIndex,
								sentence.length
							);
							if (range) {
								newlyFoundRanges.push(range);
								foundCount++;
								if (foundCount >= limit) break;
							}
						}
					}
				}

				highlightCache.value.set(field, newlyFoundRanges);
				return newlyFoundRanges;
			};

			const highlightTextFields = ({ side, fields, highlightType }) => {
				if (
					(side === "left" && props.divId !== "div1") ||
					(side === "right" && props.divId !== "div3")
				)
					return;

				clearTextHighlights();

				const highlightClass =
					highlightType === "chain"
						? `chain-highlight-${side}`
						: `step-highlight-${side}`;
				const rangesToApply = [];

				fields.forEach(field => {
					let rangesForField;
					if (highlightCache.value.has(field)) {
						rangesForField = highlightCache.value.get(field);
					} else {
						rangesForField = calculateAndCacheRangesForField(field);
					}
					rangesToApply.push(...rangesForField);
				});

				if (rangesToApply.length > 0) {
					requestAnimationFrame(() => {
						const clonedRanges = rangesToApply.map(r => r.cloneRange());
						clonedRanges.reverse().forEach(range => {
							const highlightSpan = document.createElement("span");
							highlightSpan.className = `sentence-highlight ${highlightClass}`;
							try {
								if (
									range.commonAncestorContainer.parentElement &&
									range.commonAncestorContainer.parentElement.classList.contains(
										"sentence-highlight"
									)
								)
									return;
								range.surroundContents(highlightSpan);
							} catch (e) {
								console.warn("Could not highlight a range.", e);
							}
						});
					});
				}
			};

			const highlightInfoboxFields = ({ side, fields, highlightType }) => {
				if (
					(side === "left" && props.divId !== "div1") ||
					(side === "right" && props.divId !== "div3")
				)
					return;

				clearInfoboxHighlights();
				const highlightClass =
					highlightType === "chain"
						? `chain-highlight-${side}`
						: `step-highlight-${side}`;

				fields.forEach(field => {
					const infobox = divRef.value.querySelector(
						".infobox, .sidebar, .toccolours"
					);
					if (infobox) {
						const rows = infobox.querySelectorAll("tr");
						for (const row of rows) {
							const th = row.querySelector("th");
							if (th && th.textContent.trim() === field) {
								row.classList.add(highlightClass);
								break;
							}
						}
					}
				});

				highlightTextFields({ side, fields, highlightType });
			};

			onMounted(() => {
				fetchWikipediaContent();
				if (divRef.value) {
					divRef.value.addEventListener("scroll", updatePopupPosition);
				}
				const hoverEvent = `hover-${
					props.divId === "div1" ? "left" : "right"
				}-infobox`;
				const unhoverEvent = `unhover-${
					props.divId === "div1" ? "left" : "right"
				}-infobox`;
				bus.on(hoverEvent, handleHoverInfobox);
				bus.on(unhoverEvent, handleUnhoverInfobox);
				bus.on(`${props.divId}Event`, ({ content, sourceId }) => {
					selectedText.value[props.divId] = content;
					showPopup.value[props.divId] = true;
					nextTick(() => {
						updatePopupPosition();
					});
				});
				bus.on("highlight-infobox", highlightInfoboxFields);
				bus.on("unhighlight-infobox", clearTextHighlights);
			});

			onUnmounted(() => {
				if (divRef.value) {
					divRef.value.removeEventListener("scroll", updatePopupPosition);
				}
				const hoverEvent = `hover-${
					props.divId === "div1" ? "left" : "right"
				}-infobox`;
				const unhoverEvent = `unhover-${
					props.divId === "div1" ? "left" : "right"
				}-infobox`;
				bus.off(hoverEvent, handleHoverInfobox);
				bus.off(unhoverEvent, handleUnhoverInfobox);
				bus.off(`${props.divId}Event`);
				bus.off("highlight-infobox", highlightInfoboxFields);
				bus.off("unhighlight-infobox", clearTextHighlights);
			});

			return {
				props,
				pageHtml,
				loading,
				error,
				selectedText,
				showPopup,
				divRef,
				fetchWikipediaContent,
				handleSelection,
				closePopup,
				updatePopupPosition
			};
		}
	};
</script>

<style scoped>
	h1 {
		text-align: center;
		margin-bottom: 20px;
		color: #2c3e50;
	}

	.div0 {
		position: relative;
		width: 55%;
		max-width: 100%;
		max-height: 100%;
		overflow: auto;
		padding: 20px;
		background-color: #ffffff;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		margin: 10px;
	}

	#div1,
	#div3 {
		width: 55%;
		max-width: 100%;
		max-height: 100%;
		overflow: auto;
		padding: 20px;
		background-color: #ffffff;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		margin: 10px;
	}

	.showHtml {
		width: 100%;
		height: 100%;
		overflow: auto;
	}

	::selection {
		background-color: rgba(255, 255, 0, 0.3);
		color: inherit;
	}
</style>

<style>
	.infobox tr.infobox-highlight th,
	.infobox tr.infobox-highlight td,
	.sidebar tr.infobox-highlight th,
	.sidebar tr.infobox-highlight td,
	.toccolours tr.infobox-highlight th,
	.toccolours tr.infobox-highlight td {
		background-color: #fffacd !important;
		box-shadow: 0 0 8px rgba(255, 235, 59, 0.8) !important;
		transition: all 0.15s ease !important;
	}

	/* 因果链高亮样式 */
	.infobox tr.step-highlight-left th,
	.infobox tr.step-highlight-left td,
	.sidebar tr.step-highlight-left th,
	.sidebar tr.step-highlight-left td {
		background-color: rgba(26, 115, 232, 0.1) !important;
		box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.3) !important;
		transition: all 0.2s ease;
	}

	.infobox tr.chain-highlight-left th,
	.infobox tr.chain-highlight-left td,
	.sidebar tr.chain-highlight-left th,
	.sidebar tr.chain-highlight-left td {
		background-color: rgba(26, 115, 232, 0.2) !important;
		box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.5) !important;
		transition: all 0.2s ease;
	}

	.infobox tr.step-highlight-right th,
	.infobox tr.step-highlight-right td,
	.sidebar tr.step-highlight-right th,
	.sidebar tr.step-highlight-right td {
		background-color: rgba(156, 39, 176, 0.1) !important;
		box-shadow: 0 0 0 2px rgba(156, 39, 176, 0.3) !important;
		transition: all 0.2s ease;
	}

	.infobox tr.chain-highlight-right th,
	.infobox tr.chain-highlight-right td,
	.sidebar tr.chain-highlight-right th,
	.sidebar tr.chain-highlight-right td {
		background-color: rgba(156, 39, 176, 0.2) !important;
		box-shadow: 0 0 0 3px rgba(156, 39, 176, 0.5) !important;
		transition: all 0.2s ease;
	}

	/* 在全局样式中添加句子高亮样式 */
	.sentence-highlight {
		border-radius: 4px;
		padding: 2px 4px;
		margin: 0 1px;
		transition: all 0.2s ease;
		display: inline;
		line-height: 1.6;
	}

	.sentence-highlight.step-highlight-left {
		background-color: rgba(26, 115, 232, 0.15) !important;
		box-shadow: 0 0 0 1px rgba(26, 115, 232, 0.3) !important;
	}

	.sentence-highlight.chain-highlight-left {
		background-color: rgba(26, 115, 232, 0.25) !important;
		box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.5) !important;
	}

	.sentence-highlight.step-highlight-right {
		background-color: rgba(156, 39, 176, 0.15) !important;
		box-shadow: 0 0 0 1px rgba(156, 39, 176, 0.3) !important;
	}

	.sentence-highlight.chain-highlight-right {
		background-color: rgba(156, 39, 176, 0.25) !important;
		box-shadow: 0 0 0 2px rgba(156, 39, 176, 0.5) !important;
	}
</style>
