const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak
} = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: "1B2A4A", type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", font: "Arial", size: 20 })] })]
  });
}

function cell(text, width, fill) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20 })] })]
  });
}

function heading1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 }, children: [new TextRun({ text, bold: true, font: "Arial", size: 32, color: "1B2A4A" })] });
}

function heading2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 160 }, children: [new TextRun({ text, bold: true, font: "Arial", size: 26, color: "2E5090" })] });
}

function para(text) {
  return new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text, font: "Arial", size: 22 })] });
}

function boldPara(label, text) {
  return new Paragraph({ spacing: { after: 120 }, children: [
    new TextRun({ text: label, bold: true, font: "Arial", size: 22 }),
    new TextRun({ text, font: "Arial", size: 22 })
  ]});
}

function bulletItem(text, ref) {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, font: "Arial", size: 22 })]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1B2A4A" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5090" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "news.etzhayyim.com \u2014 Marketing & Monetization Strategy", font: "Arial", size: 16, color: "888888" })] })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Page ", font: "Arial", size: 16, color: "888888" }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" })] })] })
    },
    children: [
      // === TITLE PAGE ===
      new Paragraph({ spacing: { before: 3000 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "news.etzhayyim.com", font: "Arial", size: 48, bold: true, color: "1B2A4A" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "\u30DE\u30FC\u30B1\u30C6\u30A3\u30F3\u30B0 & \u30DE\u30CD\u30BF\u30A4\u30BA\u6226\u7565\u66F8", font: "Arial", size: 36, color: "2E5090" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Marketing & Monetization Strategy", font: "Arial", size: 28, color: "666666" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: "2026\u5E742\u6708 | \u30A2\u30CB\u30E1\u30FB\u30B2\u30FC\u30E0\u30FB\u30DE\u30F3\u30AC \u30CB\u30E5\u30FC\u30B9\u30E1\u30C7\u30A3\u30A2", font: "Arial", size: 22, color: "888888" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E5090", space: 1 } }, children: [] }),

      new Paragraph({ children: [new PageBreak()] }),

      // === 1. EXECUTIVE SUMMARY ===
      heading1("1. \u30A8\u30B0\u30BC\u30AF\u30C6\u30A3\u30D6\u30B5\u30DE\u30EA\u30FC"),
      para("news.etzhayyim.com\u306F\u3001\u65E5\u672C\u306E\u30B2\u30FC\u30E0\u30E1\u30FC\u30AB\u30FC\u30FBPS5/Switch\u30D7\u30E9\u30C3\u30C8\u30D5\u30A9\u30FC\u30E0\u3092\u4E2D\u5FC3\u306B\u3001\u30A2\u30CB\u30E1\u30FB\u30B2\u30FC\u30E0\u30FB\u30DE\u30F3\u30AC\u306E\u30CB\u30E5\u30FC\u30B9\u3092\u591A\u8A00\u8A9E\uFF0812\u8A00\u8A9E\uFF09\u3067\u914D\u4FE1\u3059\u308B\u81EA\u5F8B\u578B\u30CB\u30E5\u30FC\u30B9\u30E1\u30C7\u30A3\u30A2\u3067\u3042\u308B\u3002"),
      para("\u53CE\u76CA\u76EE\u6A19\u306F\u6708\u9593100\u4E07\u5186\uFF08ExoClick\u5E83\u544A\u53CE\u5165\uFF09\u3002\u521D\u5FC3\u8005\u5411\u3051\u30D7\u30E9\u30A4\u30DE\u30FC\u8A18\u4E8B\u3092\u8EF8\u306B\u3001SEO\u30C8\u30E9\u30D5\u30A3\u30C3\u30AF\u3068ExoClick\u5E83\u544A\u6700\u9069\u5316\u3067\u53CE\u76CA\u5316\u3092\u56F3\u308B\u3002"),
      boldPara("\u30BF\u30FC\u30B2\u30C3\u30C8\u8AAD\u8005: ", "\u30A2\u30CB\u30E1\u30FB\u30B2\u30FC\u30E0\u521D\u5FC3\u8005\uFF08\u65B0\u898F\u30D5\u30A1\u30F3\u3001\u5225\u30B8\u30E3\u30F3\u30EB\u304B\u3089\u306E\u6D41\u5165\u8005\uFF09"),
      boldPara("\u53CE\u76CA\u30E2\u30C7\u30EB: ", "ExoClick\u30C7\u30A3\u30B9\u30D7\u30EC\u30A4\u5E83\u544A + \u30DD\u30C3\u30D7\u30A2\u30F3\u30C0\u30FC"),
      boldPara("\u5C55\u958B\u8A00\u8A9E: ", "ja, en, es, bn, gu, hi, kn, ml, mr, pa, ta, te"),

      new Paragraph({ children: [new PageBreak()] }),

      // === 2. TARGET AUDIENCE ===
      heading1("2. \u30BF\u30FC\u30B2\u30C3\u30C8\u30AA\u30FC\u30C7\u30A3\u30A8\u30F3\u30B9"),
      heading2("2.1 \u30DA\u30EB\u30BD\u30CA\u5B9A\u7FA9"),
      para("\u4E3B\u8981\u30DA\u30EB\u30BD\u30CA\u306F\u300C\u30A2\u30CB\u30E1\u30FB\u30B2\u30FC\u30E0\u306B\u8208\u5473\u3092\u6301\u3061\u59CB\u3081\u305F\u304C\u3001\u4F55\u304B\u3089\u59CB\u3081\u308C\u3070\u3044\u3044\u304B\u308F\u304B\u3089\u306A\u3044\u5C64\u300D\u3002SNS\u3084\u52D5\u753B\u30B5\u30A4\u30C8\u3067\u4EBA\u6C17\u4F5C\u54C1\u306E\u65AD\u7247\u3092\u898B\u3066\u3001\u6DF1\u304F\u77E5\u308A\u305F\u3044\u3068\u611F\u3058\u305F\u5C64\u3092\u60F3\u5B9A\u3059\u308B\u3002"),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 3510, 3510],
        rows: [
          new TableRow({ children: [headerCell("\u30BB\u30B0\u30E1\u30F3\u30C8", 2340), headerCell("\u7279\u5FB4", 3510), headerCell("\u30B3\u30F3\u30C6\u30F3\u30C4\u30CB\u30FC\u30BA", 3510)] }),
          new TableRow({ children: [cell("\u30A2\u30CB\u30E1\u5165\u9580\u8005", 2340, "F0F5FF"), cell("SNS\u3067\u5207\u308A\u629C\u304D\u3092\u898B\u3066\u8208\u5473\u3002\u4F5C\u54C1\u6570\u304C\u591A\u304F\u3066\u4F55\u304B\u3089\u89B3\u308C\u3070\u3044\u3044\u304B\u8FF7\u3046", 3510), cell("\u8996\u8074\u9806\u5E8F\u30AC\u30A4\u30C9\u3001\u30AD\u30E3\u30E9\u7D39\u4ECB\u3001\u4F5C\u54C1\u6982\u8981", 3510)] }),
          new TableRow({ children: [cell("\u30B2\u30FC\u30E0\u521D\u5FC3\u8005", 2340, "F0F5FF"), cell("\u8A71\u984C\u306E\u65B0\u4F5C\u3092\u8CB7\u3046\u304B\u8FF7\u3063\u3066\u3044\u308B\u3002\u64CD\u4F5C\u3084\u30B7\u30B9\u30C6\u30E0\u304C\u96E3\u3057\u305D\u3046\u3067\u4E0D\u5B89", 3510), cell("\u521D\u5FC3\u8005\u5411\u3051\u6B66\u5668\u30AC\u30A4\u30C9\u3001\u5E8F\u76E4\u653B\u7565\u3001\u30B7\u30B9\u30C6\u30E0\u89E3\u8AAC", 3510)] }),
          new TableRow({ children: [cell("\u30A4\u30F3\u30C9\u7CFB\u8A00\u8A9E\u5708\u8AAD\u8005", 2340, "F0F5FF"), cell("\u65E5\u672C\u30A2\u30CB\u30E1/\u30B2\u30FC\u30E0\u306E\u60C5\u5831\u3092\u6BCD\u8A9E\u3067\u8AAD\u307F\u305F\u3044\u3002\u82F1\u8A9E/\u65E5\u672C\u8A9E\u30BD\u30FC\u30B9\u306F\u30CF\u30FC\u30C9\u30EB\u304C\u9AD8\u3044", 3510), cell("\u30ED\u30FC\u30AB\u30E9\u30A4\u30BA\u3055\u308C\u305F\u30D7\u30E9\u30A4\u30DE\u30FC\u3001\u30CB\u30E5\u30FC\u30B9\u8A18\u4E8B", 3510)] }),
        ]
      }),

      heading2("2.2 \u30C8\u30E9\u30D5\u30A3\u30C3\u30AF\u6E90"),
      bulletItem("\u30AA\u30FC\u30AC\u30CB\u30C3\u30AF\u691C\u7D22\uFF08Google/Bing\uFF09\u2014 \u300C\u4F5C\u54C1\u540D + \u521D\u5FC3\u8005\u300D\u300C\u4F5C\u54C1\u540D + \u89B3\u308B\u9806\u756A\u300D\u7B49\u306E\u30AF\u30A8\u30EA", "bullets"),
      bulletItem("SNS\u7D4C\u7531\uFF08X/Twitter, Reddit, YouTube\u30B3\u30E1\u30F3\u30C8\u6B04\u304B\u3089\u306E\u6D41\u5165\uFF09", "bullets"),
      bulletItem("\u30EA\u30D5\u30A1\u30E9\u30EB\uFF08\u30A2\u30CB\u30E1\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30B5\u30A4\u30C8\u3001Wiki\u304B\u3089\u306E\u30EA\u30F3\u30AF\uFF09", "bullets"),

      new Paragraph({ children: [new PageBreak()] }),

      // === 3. CONTENT STRATEGY ===
      heading1("3. \u30B3\u30F3\u30C6\u30F3\u30C4\u6226\u7565"),
      heading2("3.1 \u8A18\u4E8B\u30BF\u30A4\u30D7\u3068\u5F79\u5272"),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [1872, 2808, 2340, 2340],
        rows: [
          new TableRow({ children: [headerCell("\u8A18\u4E8B\u30BF\u30A4\u30D7", 1872), headerCell("\u5185\u5BB9", 2808), headerCell("SEO\u5F79\u5272", 2340), headerCell("\u53CE\u76CA\u8CA2\u732E", 2340)] }),
          new TableRow({ children: [cell("\u30D7\u30E9\u30A4\u30DE\u30FC", 1872, "F0F5FF"), cell("\u4F5C\u54C1\u6982\u8981\u3001\u8996\u8074\u9806\u5E8F\u3001\u30AD\u30E3\u30E9\u7D39\u4ECB\u3001\u521D\u5FC3\u8005\u30AC\u30A4\u30C9", 2808), cell("\u30ED\u30F3\u30B0\u30C6\u30FC\u30EB\u30AD\u30FC\u30EF\u30FC\u30C9\u3092\u7372\u5F97\u3002\u5E38\u7DD1\u30C8\u30E9\u30D5\u30A3\u30C3\u30AF", 2340), cell("\u6ED1\u5728\u6642\u9593\u304C\u9577\u304F\u5E83\u544A\u8868\u793A\u56DE\u6570\u304C\u591A\u3044", 2340)] }),
          new TableRow({ children: [cell("\u30CB\u30E5\u30FC\u30B9", 1872, "F0F5FF"), cell("\u65B0\u4F5C\u767A\u8868\u3001\u30A2\u30C3\u30D7\u30C7\u30FC\u30C8\u3001\u30EA\u30EA\u30FC\u30B9\u65E5", 2808), cell("\u30C8\u30EC\u30F3\u30C9\u30AD\u30FC\u30EF\u30FC\u30C9\u3067\u77ED\u671F\u30D0\u30FC\u30B9\u30C8", 2340), cell("PV\u5358\u4FA1\u306F\u4F4E\u3044\u304C\u91CF\u3067\u7A3C\u3050", 2340)] }),
          new TableRow({ children: [cell("\u8003\u5BDF\u30FB\u5206\u6790", 1872, "F0F5FF"), cell("\u30C6\u30FC\u30DE\u8003\u5BDF\u3001\u30D0\u30C8\u30EB\u5206\u6790\u3001\u30E1\u30BF\u60C5\u5831", 2808), cell("\u6A29\u5A01\u6027\u69CB\u7BC9\u3002\u88AB\u30EA\u30F3\u30AF\u7372\u5F97", 2340), cell("\u30EA\u30D4\u30FC\u30C8\u8AAD\u8005\u3092\u80B2\u3066\u308B", 2340)] }),
        ]
      }),

      heading2("3.2 \u591A\u8A00\u8A9E\u5C55\u958B\u6226\u7565"),
      para("\u65E5\u672C\u8A9E\u3067\u30AA\u30EA\u30B8\u30CA\u30EB\u8A18\u4E8B\u3092\u4F5C\u6210\u3057\u300111\u8A00\u8A9E\u306B\u5C55\u958B\u3059\u308B\u3002\u7279\u306B\u30A4\u30F3\u30C9\u7CFB\u8A00\u8A9E\uFF08hi, bn, ta, te, mr, gu, kn, ml, pa\uFF09\u306F\u7AF6\u5408\u304C\u5C11\u306A\u304F\u3001\u30A2\u30CB\u30E1\u30FB\u30B2\u30FC\u30E0\u306E\u9700\u8981\u304C\u6025\u6210\u9577\u3057\u3066\u3044\u308B\u5E02\u5834\u3067\u3042\u308B\u3002"),
      bulletItem("\u512A\u5148\u8A00\u8A9E: ja\uFF08\u30AA\u30EA\u30B8\u30CA\u30EB\uFF09\u2192 en \u2192 hi \u2192 es \u2192 \u305D\u306E\u4ED6\u30A4\u30F3\u30C9\u7CFB\u8A00\u8A9E", "bullets"),
      bulletItem("\u30AD\u30FC\u30EF\u30FC\u30C9\u8ABF\u67FB\u306F\u8A00\u8A9E\u3054\u3068\u306B\u5B9F\u65BD\u3002\u540C\u3058\u4F5C\u54C1\u3067\u3082\u691C\u7D22\u30AF\u30A8\u30EA\u306F\u8A00\u8A9E\u306B\u3088\u3063\u3066\u7570\u306A\u308B", "bullets"),
      bulletItem("\u56FA\u6709\u540D\u8A5E\u306F\u5404\u8A00\u8A9E\u306E\u516C\u5F0F\u8868\u8A18\u306B\u5F93\u3046\uFF08\u30A8\u30C7\u30A3\u30C8\u30EA\u30A2\u30EB\u30AC\u30A4\u30C9\u30E9\u30A4\u30F3\u6E96\u62E0\uFF09", "bullets"),

      heading2("3.3 \u30B3\u30F3\u30C6\u30F3\u30C4\u30D1\u30A4\u30D7\u30E9\u30A4\u30F3"),
      para("\u65E2\u5B58\u306E\u81EA\u52D5\u5316\u30B9\u30AF\u30EA\u30D7\u30C8\uFF08generate_bulk_articles.py, generate_series_primers_from_registries.py\uFF09\u3092\u6D3B\u7528\u3057\u3001\u4EE5\u4E0B\u306E\u30D5\u30ED\u30FC\u3067\u914D\u4FE1\u3059\u308B\u3002"),
      bulletItem("\u30BD\u30FC\u30B9\u53CE\u96C6\uFF08AniList/Steam API\uFF09\u2192 \u30EC\u30B8\u30B9\u30C8\u30EA\u66F4\u65B0 \u2192 \u8A18\u4E8B\u751F\u6210 \u2192 \u54C1\u8CEA\u30C1\u30A7\u30C3\u30AF \u2192 \u591A\u8A00\u8A9E\u5C55\u958B \u2192 \u516C\u958B", "bullets"),

      new Paragraph({ children: [new PageBreak()] }),

      // === 4. SEO STRATEGY ===
      heading1("4. SEO\u6226\u7565"),
      heading2("4.1 \u30AD\u30FC\u30EF\u30FC\u30C9\u6226\u7565"),
      para("\u521D\u5FC3\u8005\u5411\u3051\u30D7\u30E9\u30A4\u30DE\u30FC\u8A18\u4E8B\u306F\u3001\u30ED\u30F3\u30B0\u30C6\u30FC\u30EB\u30AD\u30FC\u30EF\u30FC\u30C9\u3092\u7372\u5F97\u3057\u3084\u3059\u3044\u3002\u4EE5\u4E0B\u306E\u30AD\u30FC\u30EF\u30FC\u30C9\u30D1\u30BF\u30FC\u30F3\u3092\u91CD\u70B9\u7684\u306B\u72D9\u3046\u3002"),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [3120, 3120, 3120],
        rows: [
          new TableRow({ children: [headerCell("\u30AD\u30FC\u30EF\u30FC\u30C9\u30D1\u30BF\u30FC\u30F3", 3120), headerCell("\u4F8B\uFF08\u65E5\u672C\u8A9E\uFF09", 3120), headerCell("\u4F8B\uFF08\u82F1\u8A9E\uFF09", 3120)] }),
          new TableRow({ children: [cell("[作品名] 初心者", 3120, "F0F5FF"), cell("呪術廻戦 初心者 おすすめ", 3120), cell("Jujutsu Kaisen beginner guide", 3120)] }),
          new TableRow({ children: [cell("[作品名] 観る順番", 3120, "F0F5FF"), cell("ワンピース 観る順番 2026", 3120), cell("One Piece watch order 2026", 3120)] }),
          new TableRow({ children: [cell("[ゲーム名] 初心者 武器", 3120, "F0F5FF"), cell("モンハンワイルズ 初心者 武器 おすすめ", 3120), cell("MH Wilds best weapon beginners", 3120)] }),
          new TableRow({ children: [cell("[ゲーム名] 序盤 攻略", 3120, "F0F5FF"), cell("エルデンリング 序盤 攻略", 3120), cell("Elden Ring early game tips", 3120)] }),
        ]
      }),

      heading2("4.2 \u5185\u90E8\u30EA\u30F3\u30AF\u69CB\u9020"),
      bulletItem("\u30D7\u30E9\u30A4\u30DE\u30FC\u8A18\u4E8B \u2192 \u30AD\u30E3\u30E9\u30AF\u30BF\u30FC\u8A18\u4E8B \u2192 \u30A8\u30D4\u30BD\u30FC\u30C9\u8003\u5BDF\u3078\u306E\u5C0E\u7DDA", "bullets"),
      bulletItem("\u30D7\u30E9\u30C3\u30C8\u30D5\u30A9\u30FC\u30E0\u30CF\u30D6\u30DA\u30FC\u30B8\uFF08PS5\u30CF\u30D6\u3001Switch\u30CF\u30D6\uFF09\u3092\u4F5C\u6210\u3057\u3001\u30C8\u30D4\u30AB\u30EB\u30AA\u30FC\u30BD\u30EA\u30C6\u30A3\u3092\u78BA\u7ACB", "bullets"),
      bulletItem("\u30E1\u30FC\u30AB\u30FC\u5225\u30DA\u30FC\u30B8\uFF08\u30AB\u30D7\u30B3\u30F3\u3001\u4EFB\u5929\u5802\u7B49\uFF09\u3092\u30AB\u30C6\u30B4\u30EA\u30CF\u30D6\u3068\u3057\u3066\u904B\u7528", "bullets"),

      heading2("4.3 \u6280\u8853\u7684SEO"),
      bulletItem("JSON-LD\u69CB\u9020\u5316\u30C7\u30FC\u30BF\u3092\u5168\u8A18\u4E8B\u306B\u57CB\u3081\u8FBC\u307F\uFF08\u65E2\u5B58\u306E\u30B9\u30AD\u30FC\u30DE\u3092\u6D3B\u7528\uFF09", "bullets"),
      bulletItem("Core Web Vitals\u6700\u9069\u5316\uFF08WASM\u30FB CDN\u3092\u6D3B\u7528\u3057\u305F\u9AD8\u901F\u914D\u4FE1\uFF09", "bullets"),
      bulletItem("hreflang\u30BF\u30B0\u306B\u3088\u308B12\u8A00\u8A9E\u5BFE\u5FDC\u306E\u660E\u793A", "bullets"),

      new Paragraph({ children: [new PageBreak()] }),

      // === 5. MONETIZATION ===
      heading1("5. \u30DE\u30CD\u30BF\u30A4\u30BA\u6226\u7565"),
      heading2("5.1 ExoClick\u5E83\u544A\u914D\u7F6E"),
      para("ExoClick\u3092\u4E3B\u8981\u53CE\u76CA\u6E90\u3068\u3057\u3001\u4EE5\u4E0B\u306E\u5E83\u544A\u30D5\u30A9\u30FC\u30DE\u30C3\u30C8\u3092\u6700\u9069\u5316\u3059\u308B\u3002"),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 2340, 2340, 2340],
        rows: [
          new TableRow({ children: [headerCell("\u30D5\u30A9\u30FC\u30DE\u30C3\u30C8", 2340), headerCell("\u914D\u7F6E\u5834\u6240", 2340), headerCell("\u671F\u5F85CPM", 2340), headerCell("\u6CE8\u610F\u70B9", 2340)] }),
          new TableRow({ children: [cell("\u30C7\u30A3\u30B9\u30D7\u30EC\u30A4\u30D0\u30CA\u30FC", 2340, "F0F5FF"), cell("\u8A18\u4E8B\u4E0A\u90E8 + \u30B5\u30A4\u30C9\u30D0\u30FC", 2340), cell("$0.10\u2013$0.50", 2340), cell("\u30D3\u30E5\u30FC\u30A2\u30D3\u30EA\u30C6\u30A3\u91CD\u8996", 2340)] }),
          new TableRow({ children: [cell("\u30DD\u30C3\u30D7\u30A2\u30F3\u30C0\u30FC", 2340, "F0F5FF"), cell("\u8A18\u4E8B\u672C\u6587\u4E2D\u9593", 2340), cell("$0.30\u2013$1.00", 2340), cell("UX\u3068\u306E\u30D0\u30E9\u30F3\u30B9\u304C\u91CD\u8981", 2340)] }),
          new TableRow({ children: [cell("\u30CD\u30A4\u30C6\u30A3\u30D6\u5E83\u544A", 2340, "F0F5FF"), cell("\u95A2\u9023\u8A18\u4E8B\u30A8\u30EA\u30A2", 2340), cell("$0.20\u2013$0.80", 2340), cell("\u30B3\u30F3\u30C6\u30F3\u30C4\u3068\u306E\u89AA\u548C\u6027", 2340)] }),
        ]
      }),

      heading2("5.2 \u53CE\u76CA\u30B7\u30DF\u30E5\u30EC\u30FC\u30B7\u30E7\u30F3"),
      para("\u6708\u9593100\u4E07\u5186\u9054\u6210\u306B\u5FC5\u8981\u306A\u30C8\u30E9\u30D5\u30A3\u30C3\u30AF\u898F\u6A21\u306E\u8A66\u7B97\u3002"),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 2340, 2340, 2340],
        rows: [
          new TableRow({ children: [headerCell("\u6307\u6A19", 2340), headerCell("\u4FDD\u5B88\u7684", 2340), headerCell("\u6A19\u6E96", 2340), headerCell("\u697D\u89B3\u7684", 2340)] }),
          new TableRow({ children: [cell("\u5E73\u5747CPM", 2340, "F0F5FF"), cell("$0.15", 2340), cell("$0.30", 2340), cell("$0.50", 2340)] }),
          new TableRow({ children: [cell("\u5FC5\u8981\u6708\u9593PV", 2340, "F0F5FF"), cell("44,400,000", 2340), cell("22,200,000", 2340), cell("13,300,000", 2340)] }),
          new TableRow({ children: [cell("\u5FC5\u8981\u65E5\u6B21PV", 2340, "F0F5FF"), cell("1,480,000", 2340), cell("740,000", 2340), cell("443,000", 2340)] }),
          new TableRow({ children: [cell("\u5FC5\u8981\u8A18\u4E8B\u6570/\u65E5", 2340, "F0F5FF"), cell("150\u2013200", 2340), cell("75\u2013100", 2340), cell("45\u201360", 2340)] }),
        ]
      }),

      para("\u203B1 USD = 150 JPY \u3067\u8A08\u7B97\u3002\u5E83\u544A\u5358\u4FA1\u306F\u30B8\u30AA\u30FB\u30AB\u30C6\u30B4\u30EA\u306B\u3088\u308A\u5909\u52D5\u3002"),

      heading2("5.3 \u53CE\u76CA\u6700\u9069\u5316\u65BD\u7B56"),
      bulletItem("A/B\u30C6\u30B9\u30C8\uFF1A\u5E83\u544A\u914D\u7F6E\u30FB\u30B5\u30A4\u30BA\u30FB\u30BF\u30A4\u30DF\u30F3\u30B0\u306E\u6700\u9069\u5316", "bullets"),
      bulletItem("\u30B8\u30AA\u30BF\u30FC\u30B2\u30C6\u30A3\u30F3\u30B0\uFF1A\u30A4\u30F3\u30C9\u5708\u30FB\u4E2D\u5357\u7C73\u306A\u3069CPM\u304C\u9AD8\u3044\u5730\u57DF\u3078\u306E\u6CE8\u529B", "bullets"),
      bulletItem("\u30E9\u30A4\u30C8\u30BB\u30FC\u30EB\u30B9\u5E83\u544A\u306E\u5F8C\u65B9\u914D\u7F6E\uFF1A\u8A18\u4E8B\u672B\u5C3E\u306B\u95A2\u9023\u30B3\u30F3\u30C6\u30F3\u30C4\u5E83\u544A\u3092\u914D\u7F6E", "bullets"),
      bulletItem("\u30DA\u30FC\u30B8\u6ED1\u5728\u6642\u9593\u306E\u5EF6\u9577\uFF1A\u30D7\u30E9\u30A4\u30DE\u30FC\u8A18\u4E8B\u306E\u5145\u5B9F\u5316\u3067\u5E83\u544A\u8868\u793A\u56DE\u6570\u3092\u5897\u3084\u3059", "bullets"),

      new Paragraph({ children: [new PageBreak()] }),

      // === 6. MARKETING CHANNELS ===
      heading1("6. \u30DE\u30FC\u30B1\u30C6\u30A3\u30F3\u30B0\u30C1\u30E3\u30CD\u30EB"),
      heading2("6.1 \u30AA\u30FC\u30AC\u30CB\u30C3\u30AF\u30C1\u30E3\u30CD\u30EB"),
      bulletItem("Google Discover\uFF1A\u753B\u50CF\u4ED8\u304D\u30CB\u30E5\u30FC\u30B9\u8A18\u4E8B\u3067\u30D5\u30A3\u30FC\u30C9\u306B\u8868\u793A\u3055\u308C\u308B\u3053\u3068\u3092\u72D9\u3046", "bullets"),
      bulletItem("Google News\uFF1A\u30CB\u30E5\u30FC\u30B9\u30B5\u30A4\u30C8\u30DE\u30C3\u30D7\u3092\u63D0\u51FA\u3057\u3001News\u30BF\u30D6\u3078\u306E\u63B2\u8F09\u3092\u76EE\u6307\u3059", "bullets"),
      bulletItem("YouTube\u691C\u7D22\uFF1A\u8A18\u4E8B\u3092\u30D9\u30FC\u30B9\u306B\u3057\u305F\u30B7\u30E7\u30FC\u30C8\u52D5\u753B\u3067\u5F15\u304D\u8FBC\u307F\uFF08\u5C06\u6765\u65BD\u7B56\uFF09", "bullets"),

      heading2("6.2 \u30BD\u30FC\u30B7\u30E3\u30EB\u30E1\u30C7\u30A3\u30A2"),
      bulletItem("X/Twitter\uFF1A\u65B0\u7740\u8A18\u4E8B\u306E\u81EA\u52D5\u6295\u7A3F\u3002\u30C8\u30EC\u30F3\u30C9\u30CF\u30C3\u30B7\u30E5\u30BF\u30B0\u306B\u5408\u308F\u305B\u305F\u914D\u4FE1", "bullets"),
      bulletItem("Reddit\uFF1A r/anime, r/gaming \u7B49\u306E\u30B3\u30DF\u30E5\u30CB\u30C6\u30A3\u3067\u4FA1\u5024\u3042\u308B\u8B70\u8AD6\u306B\u53C2\u52A0\u3057\u3001\u81EA\u7136\u306A\u5F62\u3067\u8A18\u4E8B\u3092\u7D39\u4ECB", "bullets"),
      bulletItem("Pinterest\uFF1A\u30A2\u30CB\u30E1\u30AD\u30E3\u30E9\u30AF\u30BF\u30FC\u56F3\u89E3\u3092\u30D4\u30F3\u3068\u3057\u3066\u6295\u7A3F\u3002\u8996\u899A\u7684\u306A\u30B3\u30F3\u30C6\u30F3\u30C4\u3067\u6D41\u5165\u3092\u7372\u5F97", "bullets"),

      heading2("6.3 \u30AF\u30ED\u30B9\u30D7\u30ED\u30E2\u30FC\u30B7\u30E7\u30F3"),
      bulletItem("\u30A2\u30CB\u30E1\u8A18\u4E8B\u304B\u3089\u30B2\u30FC\u30E0\u8A18\u4E8B\u3078\u306E\u8A98\u5C0E\uFF08\u4F8B\uFF1A\u300E\u9B3C\u6EC5\u306E\u5203\u300F\u30D5\u30A1\u30F3\u2192\u300E\u9B3C\u6EC5\u306E\u5203 \u30D2\u30CE\u30AB\u30DF\u8A18\u300F\u30B2\u30FC\u30E0\u30EC\u30D3\u30E5\u30FC\uFF09", "bullets"),
      bulletItem("\u30B7\u30EA\u30FC\u30BA\u30CF\u30D6\u30DA\u30FC\u30B8\u3092\u6D3B\u7528\u3057\u305F\u56DE\u904A\u7387\u5411\u4E0A", "bullets"),

      new Paragraph({ children: [new PageBreak()] }),

      // === 7. KPI & MILESTONES ===
      heading1("7. KPI\u3068\u30DE\u30A4\u30EB\u30B9\u30C8\u30FC\u30F3"),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [1560, 1560, 1560, 1560, 1560, 1560],
        rows: [
          new TableRow({ children: [headerCell("KPI", 1560), headerCell("M1", 1560), headerCell("M3", 1560), headerCell("M6", 1560), headerCell("M9", 1560), headerCell("M12", 1560)] }),
          new TableRow({ children: [cell("\u8A18\u4E8B\u6570/\u65E5", 1560, "F0F5FF"), cell("20", 1560), cell("50", 1560), cell("80", 1560), cell("100", 1560), cell("100+", 1560)] }),
          new TableRow({ children: [cell("\u65E5\u6B21PV", 1560, "F0F5FF"), cell("5,000", 1560), cell("50,000", 1560), cell("200,000", 1560), cell("500,000", 1560), cell("740,000+", 1560)] }),
          new TableRow({ children: [cell("\u5E83\u544A\u53CE\u5165/\u6708", 1560, "F0F5FF"), cell("\u00A52,000", 1560), cell("\u00A530,000", 1560), cell("\u00A5200,000", 1560), cell("\u00A5600,000", 1560), cell("\u00A51,000,000", 1560)] }),
          new TableRow({ children: [cell("\u5BFE\u5FDC\u8A00\u8A9E\u6570", 1560, "F0F5FF"), cell("3", 1560), cell("6", 1560), cell("9", 1560), cell("12", 1560), cell("12", 1560)] }),
          new TableRow({ children: [cell("\u30E1\u30FC\u30AB\u30FC\u30AB\u30D0\u30FC\u7387", 1560, "F0F5FF"), cell("5/15", 1560), cell("10/15", 1560), cell("13/15", 1560), cell("15/15", 1560), cell("15/15", 1560)] }),
        ]
      }),

      new Paragraph({ spacing: { before: 200 }, children: [] }),

      heading1("8. \u30EA\u30B9\u30AF\u3068\u5BFE\u7B56"),
      bulletItem("\u30B3\u30F3\u30C6\u30F3\u30C4\u54C1\u8CEA\u30EA\u30B9\u30AF\uFF1Aquality_check_content.py\u306B\u3088\u308B\u81EA\u52D5\u30C1\u30A7\u30C3\u30AF + \u30A8\u30C7\u30A3\u30C8\u30EA\u30A2\u30EB\u30AC\u30A4\u30C9\u30E9\u30A4\u30F3\u9075\u5B88", "bullets"),
      bulletItem("\u5E83\u544A\u5358\u4FA1\u5909\u52D5\u30EA\u30B9\u30AF\uFF1A\u8907\u6570\u5E83\u544A\u30D5\u30A9\u30FC\u30DE\u30C3\u30C8\u3092\u4F75\u7528\u3057\u3001\u5358\u4E00\u4F9D\u5B58\u3092\u907F\u3051\u308B", "bullets"),
      bulletItem("Google\u30A2\u30EB\u30B4\u30EA\u30BA\u30E0\u5909\u66F4\u30EA\u30B9\u30AF\uFF1A\u591A\u8A00\u8A9E\u5C55\u958B\u3067\u5730\u57DF\u5206\u6563\u3002\u7279\u5B9A\u5730\u57DF\u3078\u306E\u4F9D\u5B58\u3092\u6E1B\u3089\u3059", "bullets"),
      bulletItem("\u8457\u4F5C\u6A29\u30EA\u30B9\u30AF\uFF1A\u30AA\u30EA\u30B8\u30CA\u30EB\u30B3\u30F3\u30C6\u30F3\u30C4\u306B\u5FB9\u3057\u3001\u4E8C\u6B21\u30BD\u30FC\u30B9\u306E\u5F15\u7528\u306F\u6700\u5C0F\u9650\u306B", "bullets"),

      new Paragraph({ spacing: { before: 400 }, border: { top: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC", space: 1 } }, children: [] }),
      para("\u672C\u6587\u66F8\u306Fnews.etzhayyim.com\u30D7\u30ED\u30B8\u30A7\u30AF\u30C8\u306E\u5185\u90E8\u6226\u7565\u8CC7\u6599\u3067\u3042\u308A\u30012026\u5E742\u6708\u6642\u70B9\u306E\u60C5\u5831\u306B\u57FA\u3065\u304F\u3002"),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/upbeat-relaxed-bardeen/mnt/etzhayyim-project-news/marketing-monetization-strategy.docx", buffer);
  console.log("Strategy document created successfully.");
});
