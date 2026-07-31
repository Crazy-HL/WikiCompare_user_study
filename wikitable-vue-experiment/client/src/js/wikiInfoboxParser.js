/**
 * 维基百科Infobox专业解析器 - 改进版
 * 增强数值提取能力，优化数据结构，保留原始值和提取值
 */
export function parseInfoboxForComparison(infoboxElement) {
    if (!infoboxElement) return null;
  
    // 1. 提取标题和基本信息
    const result = {
      title: extractTitle(infoboxElement),
      type: detectInfoboxType(infoboxElement),
      sections: {}
    };
  
    // 2. 按section分组处理数据
    let currentSection = "基本信息";
    const rows = infoboxElement.querySelectorAll('tr');
  
    rows.forEach(row => {
      // 2.1 处理section标题行
      if (row.classList.contains('infobox-header') || row.querySelector('th[colspan="2"].infobox-header')) {
        currentSection = cleanText(row.textContent) || currentSection;
        result.sections[currentSection] = result.sections[currentSection] || {};
        return;
      }
  
      // 2.2 处理普通数据行
      const th = row.querySelector('th.infobox-label');
      const td = row.querySelector('td.infobox-data');
      if (!th || !td) return;
  
      const key = cleanFieldName(th.textContent);
      const value = extractEnhancedValue(td);
  
      if (key && value) {
        result.sections[currentSection] = result.sections[currentSection] || {};
        result.sections[currentSection][key] = value;
      }
    });
  
    return result;
  }
  
  /* 增强版值提取函数 */
  function extractEnhancedValue(tdElement) {
    const td = tdElement.cloneNode(true);
    
    // 移除不需要的元素
    ['img', 'sup', '.reference', '.mw-editsection', 'abbr'].forEach(selector => {
      td.querySelectorAll(selector).forEach(el => el.remove());
    });
  
    const text = cleanText(td.textContent);
    
    // 特殊处理包含列表的情况
    if (td.querySelector('ul, ol')) {
      return Array.from(td.querySelectorAll('li')).map(li => {
        return extractValueFromText(cleanText(li.textContent));
      });
    }
    
    return extractValueFromText(text);
  }
  
  /* 增强版值提取逻辑 */
  function extractValueFromText(text) {
    // 0. 原始文本
    const raw = text;
    
    // 1. 提取百分比值 (如 "6.8%")
    const percentMatch = text.match(/(\d+\.?\d*)%/);
    if (percentMatch) {
      return {
        value: parseFloat(percentMatch[1]),
        unit: "%",
        type: "percentage",
        raw,
        extracted: true
      };
    }
  
    // 2. 增强货币值提取 (支持多种货币和单位)
    const currencyMatch = text.match(/([\$¥€£])\s*([\d,.]+)\s*(万?亿?[美元]?|million|billion|trillion)?/i);
    if (currencyMatch) {
      const currency = currencyMatch[1];
      let value = parseFloat(currencyMatch[2].replace(/,/g, ''));
      const unit = currencyMatch[3] ? currencyMatch[3].toLowerCase() : '';
      
      // 处理单位换算
      if (unit.includes('million') || unit.includes('万')) value *= 1e6;
      if (unit.includes('billion') || unit.includes('亿')) value *= 1e9;
      if (unit.includes('trillion') || unit.includes('万亿')) value *= 1e12;
      
      return {
        value,
        currency,
        unit: unit || currency,
        type: "currency",
        raw,
        extracted: true
      };
    }
  
    // 3. 增强纯数字提取 (支持千分位分隔符)
    const numberMatch = text.match(/(^|[\s(])([\d,.]+)(?=[\s)])/);
    if (numberMatch) {
      const numStr = numberMatch[2].replace(/,/g, '');
      const numValue = parseFloat(numStr);
      if (!isNaN(numValue)) {
        return {
          value: numValue,
          type: "number",
          raw,
          extracted: true
        };
      }
    }
  
    // 4. 增强排名信息提取 (支持多种格式)
    const rankMatch = text.match(/(第\s*([零一二三四五六七八九十百千万\d]+)\s*名|rank\s*(\d+)|(\d+)(?:st|nd|rd|th)\s*place)/i);
    if (rankMatch) {
      const rankValue = rankMatch[2] ? chineseToNumber(rankMatch[2]) : 
                       rankMatch[3] ? parseInt(rankMatch[3]) : 
                       parseInt(rankMatch[4]);
      return {
        rank: rankValue,
        type: "rank",
        raw,
        extracted: true
      };
    }
  
    // 5. 提取年份数据 (如 "(2023)" 或 "as of 2023")
    const yearMatch = text.match(/(?:\(|as of\s)(\d{4})\)?/i);
    const year = yearMatch ? parseInt(yearMatch[1]) : null;
  
    // 6. 提取日期范围 (如 "1 April - 31 March")
    const dateRangeMatch = text.match(/(\d{1,2}\s+[A-Za-z]+\s*[-–]\s*\d{1,2}\s+[A-Za-z]+)/i);
    if (dateRangeMatch) {
      return {
        value: dateRangeMatch[1],
        type: "date_range",
        raw,
        extracted: true
      };
    }
  
    // 7. 默认返回处理后的文本
    return {
      value: text,
      ...(year && { year }),
      type: "text",
      raw,
      extracted: false
    };
  }
  
  /* 辅助函数 - 保持不变 */
  function extractTitle(element) {
    const sources = [
      () => element.querySelector('caption')?.textContent,
      () => element.querySelector('.infobox-title')?.textContent,
      () => element.querySelector('th[colspan="2"]')?.textContent
    ];
    
    for (const source of sources) {
      const title = cleanText(source());
      if (title) return title;
    }
    return "无标题";
  }
  
  function detectInfoboxType(element) {
    const classText = `${element.className} ${element.textContent}`.toLowerCase();
    if (/country|nation|state|国家/.test(classText)) return "国家";
    if (/economy|经济/.test(classText)) return "经济";
    if (/person|people|人物/.test(classText)) return "人物";
    if (/company|公司/.test(classText)) return "公司";
    return "其他";
  }
  
  function cleanFieldName(text) {
    return cleanText(text)
      .replace(/[:：]$/, '')
      .replace(/\s+/g, ' ')
      .trim();
  }
  
  function cleanText(text) {
    return (text || "")
      .replace(/\[\d+\]/g, '')      // 去除引用标记[1]
      .replace(/\s+/g, ' ')         // 合并空格
      .replace(/[[\]]/g, '')        // 去除方括号
      .trim();
  }
  
  /* 中文数字转换 - 增强版 */
  function chineseToNumber(chinese) {
    const map = { 
      零:0, 一:1, 二:2, 三:3, 四:4, 五:5, 六:6, 七:7, 八:8, 九:9, 
      十:10, 百:100, 千:1000, 万:10000, 亿:1e8
    };
    
    let total = 0;
    let current = 0;
    
    for (let i = 0; i < chinese.length; i++) {
      const char = chinese[i];
      if (map[char] < 10) {
        current = map[char];
      } else {
        if (current === 0) current = 1;
        total += current * map[char];
        current = 0;
      }
    }
    
    return total + current;
  }