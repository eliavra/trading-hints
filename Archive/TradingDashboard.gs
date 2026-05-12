// ====================================================================
// TRADING DASHBOARD - Google Apps Script
// ====================================================================
// 1. Open a new Google Sheet
// 2. Extensions → Apps Script
// 3. Delete existing code, paste this entire file
// 4. Click Run → setupTradingDashboard
// 5. Authorize when prompted, wait ~30s for setup
// ====================================================================

var SECTORS = [
  ['Technology', 'XLK'],
  ['Financials', 'XLF'],
  ['Energy', 'XLE'],
  ['Healthcare', 'XLV'],
  ['Industrials', 'XLI'],
  ['Communication', 'XLC'],
  ['Consumer Disc.', 'XLY'],
  ['Consumer Staples', 'XLP'],
  ['Utilities', 'XLU'],
  ['Real Estate', 'XLRE'],
  ['Materials', 'XLB']
];

var TICKER_ROW = 27;

function setupTradingDashboard() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.rename('Trading Dashboard');

  var marketInput = getOrCreateSheet_(ss, 'Market_Input');
  var dataCalc = getOrCreateSheet_(ss, 'Data_Calculations');
  var dashboard = getOrCreateSheet_(ss, 'Dashboard');

  removeDefaultSheet_(ss);

  buildMarketInput_(marketInput);
  buildDataCalculations_(dataCalc);
  buildDashboard_(dashboard);

  ss.setActiveSheet(dashboard);
  SpreadsheetApp.flush();
}

function getOrCreateSheet_(ss, name) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  sheet.clear();
  sheet.clearFormats();
  sheet.clearConditionalFormatRules();
  return sheet;
}

function removeDefaultSheet_(ss) {
  try {
    var s = ss.getSheetByName('Sheet1');
    if (s && ss.getSheets().length > 1) ss.deleteSheet(s);
  } catch (e) {}
}

// ====================================================================
// MARKET_INPUT TAB
// ====================================================================
function buildMarketInput_(sheet) {
  sheet.getRange('A1:C1')
    .setValues([['Indicator', 'Current Value', 'Source / Notes']])
    .setFontWeight('bold').setBackground('#4472C4').setFontColor('#FFFFFF');

  sheet.getRange('A2:C7').setValues([
    ['% Stocks > SMA 20', 80, 'StockCharts / Finviz'],
    ['% Stocks > SMA 50', 45, 'StockCharts / Finviz'],
    ['% Stocks > SMA 200', 60, 'StockCharts / Finviz'],
    ['AAII Bull-Bear Spread', 10, 'AAII.com (% Bulls - % Bears)'],
    ['New Highs - New Lows Trend', 'Positive', 'StockCharts NH-NL Line'],
    ['Volume Breadth Trend', 'Positive', 'StockCharts Up/Down Volume']
  ]);

  sheet.getRange('A1:C7').setBorder(true, true, true, true, true, true);

  // Daily Breadth Tracker
  sheet.getRange('A9').setValue('DAILY BREADTH TRACKER')
    .setFontWeight('bold').setFontSize(11);
  sheet.getRange('A9:I9').setBackground('#D9E2F3');

  sheet.getRange('A10:I10')
    .setValues([['Date', 'New Highs', 'New Lows', 'NH-NL Net', 'NH-NL Cumul.',
                 'Up Vol (M)', 'Down Vol (M)', 'Vol Net', 'Vol Cumul.']])
    .setFontWeight('bold').setBackground('#E2EFDA');

  sheet.getRange('A11').setValue(new Date());
  sheet.getRange('B11:C11').setValues([[150, 50]]);
  sheet.getRange('D11').setFormula('=B11-C11');
  sheet.getRange('E11').setFormula('=D11');
  sheet.getRange('F11:G11').setValues([[3500, 2000]]);
  sheet.getRange('H11').setFormula('=F11-G11');
  sheet.getRange('I11').setFormula('=H11');

  sheet.getRange('A12').setValue(new Date(Date.now() + 86400000));
  sheet.getRange('B12:C12').setValues([[120, 80]]);
  sheet.getRange('D12').setFormula('=B12-C12');
  sheet.getRange('E12').setFormula('=D12+E11');
  sheet.getRange('F12:G12').setValues([[2800, 2500]]);
  sheet.getRange('H12').setFormula('=F12-G12');
  sheet.getRange('I12').setFormula('=H12+I11');

  sheet.getRange('A10:I12').setBorder(true, true, true, true, true, true);

  sheet.setColumnWidth(1, 220);
  sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 260);
  for (var i = 4; i <= 9; i++) sheet.setColumnWidth(i, 110);
  sheet.setFrozenRows(1);
}

// ====================================================================
// DATA_CALCULATIONS TAB
// ====================================================================
function buildDataCalculations_(sheet) {
  sheet.getRange('A1').setValue('Ticker').setFontWeight('bold');
  sheet.getRange('B1').setFormula("='Dashboard'!B" + TICKER_ROW)
    .setFontWeight('bold').setFontSize(12).setFontColor('#C00000');

  // 10 years weekly close via GOOGLEFINANCE
  sheet.getRange('A3').setFormula(
    '=GOOGLEFINANCE(B1,"close",DATE(YEAR(TODAY())-10,MONTH(TODAY()),DAY(TODAY())),TODAY(),"WEEKLY")'
  );

  // Calculated columns via ARRAYFORMULA
  sheet.getRange('C3').setValue('Return %').setFontWeight('bold');
  sheet.getRange('D3').setValue('Month').setFontWeight('bold');
  sheet.getRange('E3').setValue('Week').setFontWeight('bold');

  sheet.getRange('C5').setFormula(
    '=ARRAYFORMULA(IF(B5:B700="","",(B5:B700-B4:B699)/B4:B699))'
  );
  sheet.getRange('D4').setFormula(
    '=ARRAYFORMULA(IF(A4:A700="","",MONTH(A4:A700)))'
  );
  sheet.getRange('E4').setFormula(
    '=ARRAYFORMULA(IF(A4:A700="","",WEEKNUM(A4:A700)))'
  );

  sheet.getRange('C5:C700').setNumberFormat('0.00%');

  buildMonthlyAggregation_(sheet);
  buildWeeklyAggregation_(sheet);

  sheet.getRange('G3:M15').setBorder(true, true, true, true, true, true);
  sheet.getRange('O3:T55').setBorder(true, true, true, true, true, true);
}

function buildMonthlyAggregation_(sheet) {
  sheet.getRange('G2').setValue('MONTHLY SEASONALITY')
    .setFontWeight('bold').setFontSize(11);
  sheet.getRange('G2:M2').setBackground('#D9E2F3');

  sheet.getRange('G3:M3')
    .setValues([['#', 'Month', 'Avg Return', 'Win Rate', 'Std Dev', 'Min', 'Max']])
    .setFontWeight('bold').setBackground('#4472C4').setFontColor('#FFFFFF');

  var nums = [];
  var formulas = [];
  for (var m = 1; m <= 12; m++) {
    nums.push([m]);
    formulas.push([
      '=TEXT(DATE(2020,' + m + ',1),"MMM")',
      '=IFERROR(AVERAGEIF($D$5:$D$700,' + m + ',$C$5:$C$700),0)',
      '=IFERROR(COUNTIFS($D$5:$D$700,' + m + ',$C$5:$C$700,">"&0)/COUNTIF($D$5:$D$700,' + m + '),0)',
      '=IFERROR(STDEV(FILTER($C$5:$C$700,$D$5:$D$700=' + m + ')),0)',
      '=IFERROR(MINIFS($C$5:$C$700,$D$5:$D$700,' + m + '),0)',
      '=IFERROR(MAXIFS($C$5:$C$700,$D$5:$D$700,' + m + '),0)'
    ]);
  }
  sheet.getRange(4, 7, 12, 1).setValues(nums);
  sheet.getRange(4, 8, 12, 6).setFormulas(formulas);
  sheet.getRange('I4:I15').setNumberFormat('0.00%');
  sheet.getRange('J4:J15').setNumberFormat('0%');
  sheet.getRange('K4:M15').setNumberFormat('0.00%');
}

function buildWeeklyAggregation_(sheet) {
  sheet.getRange('O2').setValue('WEEKLY SEASONALITY')
    .setFontWeight('bold').setFontSize(11);
  sheet.getRange('O2:T2').setBackground('#D9E2F3');

  sheet.getRange('O3:T3')
    .setValues([['Week #', 'Avg Return', 'Win Rate', 'Std Dev', 'Min', 'Max']])
    .setFontWeight('bold').setBackground('#4472C4').setFontColor('#FFFFFF');

  var nums = [];
  var formulas = [];
  for (var w = 1; w <= 52; w++) {
    nums.push([w]);
    formulas.push([
      '=IFERROR(AVERAGEIF($E$5:$E$700,' + w + ',$C$5:$C$700),0)',
      '=IFERROR(COUNTIFS($E$5:$E$700,' + w + ',$C$5:$C$700,">"&0)/COUNTIF($E$5:$E$700,' + w + '),0)',
      '=IFERROR(STDEV(FILTER($C$5:$C$700,$E$5:$E$700=' + w + ')),0)',
      '=IFERROR(MINIFS($C$5:$C$700,$E$5:$E$700,' + w + '),0)',
      '=IFERROR(MAXIFS($C$5:$C$700,$E$5:$E$700,' + w + '),0)'
    ]);
  }
  sheet.getRange(4, 15, 52, 1).setValues(nums);
  sheet.getRange(4, 16, 52, 5).setFormulas(formulas);
  sheet.getRange('P4:P55').setNumberFormat('0.00%');
  sheet.getRange('Q4:Q55').setNumberFormat('0%');
  sheet.getRange('R4:T55').setNumberFormat('0.00%');
}

// ====================================================================
// DASHBOARD TAB
// ====================================================================
function buildDashboard_(sheet) {
  // Title
  sheet.getRange('A1:G1').mergeAcross()
    .setValue('TRADING DASHBOARD')
    .setFontWeight('bold').setFontSize(16).setFontColor('#FFFFFF')
    .setBackground('#1F3864').setHorizontalAlignment('center');

  buildPanel1_(sheet);
  buildPanel2_(sheet);
  buildPanel3_(sheet);
  applyConditionalFormatting_(sheet);

  sheet.setColumnWidth(1, 280);
  sheet.setColumnWidth(2, 130);
  sheet.setColumnWidth(3, 140);
  sheet.setColumnWidth(4, 280);
  sheet.setColumnWidth(5, 110);
  sheet.setColumnWidth(6, 110);
  sheet.setColumnWidth(7, 100);
  sheet.setFrozenRows(1);
}

// ====================================================================
// PANEL 1: MARKET BREATHING ROOM
// ====================================================================
function buildPanel1_(sheet) {
  sheet.getRange('A3:G3').mergeAcross()
    .setValue('PANEL 1: MARKET BREATHING ROOM (EXPOSURE CONTROL)')
    .setFontWeight('bold').setFontSize(12).setFontColor('#1F3864').setBackground('#D6DCE4');

  sheet.getRange('A4:D4')
    .setValues([['Indicator', 'Value', 'Signal', 'Action']])
    .setFontWeight('bold').setBackground('#4472C4').setFontColor('#FFFFFF');

  var labels = [
    '% Stocks > SMA 20 (Short-Term)',
    '% Stocks > SMA 50 (Medium-Term)',
    '% Stocks > SMA 200 (Long-Term)',
    'AAII Bull-Bear Spread (Contrarian)',
    'New Highs - New Lows (Cumulative)',
    'Volume Breadth (Up vs Down)'
  ];

  var valueFormulas = [
    "='Market_Input'!B2",
    "='Market_Input'!B3",
    "='Market_Input'!B4",
    "='Market_Input'!B5",
    "='Market_Input'!B6",
    "='Market_Input'!B7"
  ];

  var signalFormulas = [
    '=IF(B5>85,"OVERBOUGHT",IF(B5<20,"OVERSOLD",IF(B5>70,"CAUTION","NEUTRAL")))',
    '=IF(B6>85,"RED LIGHT",IF(B6<30,"GREEN LIGHT",IF(B6>75,"CAUTION","NEUTRAL")))',
    '=IF(B7>80,"STRONG BULL",IF(B7<40,"WEAK / BEAR",IF(B7<60,"CAUTION","HEALTHY")))',
    '=IF(B8>20,"EUPHORIA",IF(B8<-20,"FEAR",IF(B8>10,"CAUTIOUS BULL","NEUTRAL")))',
    '=IF(B9="Positive","HEALTHY",IF(B9="Negative","DIVERGENCE","--"))',
    '=IF(B10="Positive","BUYING",IF(B10="Negative","SELLING","--"))'
  ];

  var actionFormulas = [
    '=IF(C5="OVERBOUGHT","Reduce Longs / Tighten Stops",IF(C5="OVERSOLD","Look for Long Entries",IF(C5="CAUTION","Be Selective","Normal Exposure")))',
    '=IF(C6="RED LIGHT","Reduce Exposure",IF(C6="GREEN LIGHT","Increase Exposure",IF(C6="CAUTION","Hedge Positions","Hold Current")))',
    '=IF(C7="STRONG BULL","Stay Long",IF(C7="WEAK / BEAR","Go Defensive",IF(C7="CAUTION","Tighten Stops","Maintain Positions")))',
    '=IF(C8="EUPHORIA","Take Profits - Contrarian SELL",IF(C8="FEAR","Contrarian BUY Signal",IF(C8="CAUTIOUS BULL","Monitor Reversal","No Edge")))',
    '=IF(C9="HEALTHY","Trend Confirmed",IF(C9="DIVERGENCE","Trend Weakening - Reduce","Update Data"))',
    '=IF(C10="BUYING","Volume Confirms Trend",IF(C10="SELLING","Distribution - Be Cautious","Update Data"))'
  ];

  for (var i = 0; i < 6; i++) {
    var r = 5 + i;
    sheet.getRange(r, 1).setValue(labels[i]);
    sheet.getRange(r, 2).setFormula(valueFormulas[i]);
    sheet.getRange(r, 3).setFormula(signalFormulas[i]);
    sheet.getRange(r, 4).setFormula(actionFormulas[i]);
  }

  sheet.getRange('A4:D10').setBorder(true, true, true, true, true, true);

  // Alternating row colors
  for (var r = 5; r <= 10; r++) {
    if (r % 2 === 1) {
      sheet.getRange(r, 1, 1, 2).setBackground('#F2F2F2');
      sheet.getRange(r, 4).setBackground('#F2F2F2');
    }
  }
}

// ====================================================================
// PANEL 2: SECTOR ROTATION RADAR
// ====================================================================
function buildPanel2_(sheet) {
  sheet.getRange('A12:G12').mergeAcross()
    .setValue('PANEL 2: SECTOR ROTATION RADAR')
    .setFontWeight('bold').setFontSize(12).setFontColor('#1F3864').setBackground('#D6DCE4');

  sheet.getRange('A13:F13')
    .setValues([['Sector', 'ETF', 'Price', 'SMA 20', '% vs SMA20', 'Signal']])
    .setFontWeight('bold').setBackground('#4472C4').setFontColor('#FFFFFF');

  var sectorValues = [];
  var sectorFormulas = [];
  for (var i = 0; i < SECTORS.length; i++) {
    var r = 14 + i;
    sectorValues.push([SECTORS[i][0], SECTORS[i][1]]);
    sectorFormulas.push([
      '=IFERROR(GOOGLEFINANCE(B' + r + ',"price"),"...")',
      '=IFERROR(AVERAGE(INDEX(GOOGLEFINANCE(B' + r + ',"close",TODAY()-35,TODAY(),"DAILY"),,2)),"...")',
      '=IFERROR((C' + r + '-D' + r + ')/D' + r + ',"--")',
      '=IF(E' + r + '="--","--",IF(E' + r + '>0.03,"HOT",IF(E' + r + '<-0.03,"COLD","NEUTRAL")))'
    ]);
  }
  sheet.getRange(14, 1, SECTORS.length, 2).setValues(sectorValues);
  sheet.getRange(14, 3, SECTORS.length, 4).setFormulas(sectorFormulas);

  var lastRow = 14 + SECTORS.length - 1;
  sheet.getRange(14, 3, SECTORS.length, 2).setNumberFormat('$#,##0.00');
  sheet.getRange(14, 5, SECTORS.length, 1).setNumberFormat('0.00%');
  sheet.getRange('A13:F' + lastRow).setBorder(true, true, true, true, true, true);

  // Alternating rows
  for (var r = 14; r <= lastRow; r++) {
    if (r % 2 === 0) {
      sheet.getRange(r, 1, 1, 4).setBackground('#F2F2F2');
    }
  }
}

// ====================================================================
// PANEL 3: STOCK SEASONALITY HUNTER
// ====================================================================
function buildPanel3_(sheet) {
  sheet.getRange('A26:G26').mergeAcross()
    .setValue('PANEL 3: STOCK SEASONALITY HUNTER')
    .setFontWeight('bold').setFontSize(12).setFontColor('#1F3864').setBackground('#D6DCE4');

  // Ticker input
  sheet.getRange('A' + TICKER_ROW).setValue('Enter Ticker →').setFontWeight('bold');
  sheet.getRange('B' + TICKER_ROW).setValue('TSLA')
    .setFontWeight('bold').setFontSize(14).setFontColor('#C00000')
    .setBackground('#FFF2CC')
    .setBorder(true, true, true, true, null, null, '#C00000',
      SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  // Current month analysis
  sheet.getRange('A28').setValue('Current Month:').setFontWeight('bold');
  sheet.getRange('B28').setFormula('=TEXT(TODAY(),"MMMM")');
  sheet.getRange('C28').setValue('Avg Return:').setFontWeight('bold');
  sheet.getRange('D28').setFormula(
    "=IFERROR(INDEX('Data_Calculations'!I$4:I$15,MONTH(TODAY())),\"Loading...\")"
  ).setNumberFormat('0.00%');

  sheet.getRange('A29').setValue('Seasonality Signal:').setFontWeight('bold');
  sheet.getRange('B29').setFormula(
    '=IF(D28="Loading...","Waiting...",IF(D28>0.01,"BULLISH MONTH",IF(D28<-0.01,"BEARISH MONTH","FLAT MONTH")))'
  );
  sheet.getRange('C29').setValue('Win Rate:').setFontWeight('bold');
  sheet.getRange('D29').setFormula(
    "=IFERROR(INDEX('Data_Calculations'!J$4:J$15,MONTH(TODAY())),\"Loading...\")"
  ).setNumberFormat('0%');

  // Monthly seasonality table
  var ts = 31; // table start row
  sheet.getRange('A30').setValue('MONTHLY SEASONALITY')
    .setFontWeight('bold').setFontSize(10);

  sheet.getRange(ts, 1, 1, 7)
    .setValues([['#', 'Month', 'Avg Return', 'Win Rate', 'Std Dev', 'Min', 'Max']])
    .setFontWeight('bold').setBackground('#4472C4').setFontColor('#FFFFFF');

  var monthNums = [];
  var monthFormulas = [];
  for (var m = 1; m <= 12; m++) {
    var dcr = m + 3;
    monthNums.push([m]);
    monthFormulas.push([
      "='Data_Calculations'!H" + dcr,
      "='Data_Calculations'!I" + dcr,
      "='Data_Calculations'!J" + dcr,
      "='Data_Calculations'!K" + dcr,
      "='Data_Calculations'!L" + dcr,
      "='Data_Calculations'!M" + dcr
    ]);
  }
  sheet.getRange(ts + 1, 1, 12, 1).setValues(monthNums);
  sheet.getRange(ts + 1, 2, 12, 6).setFormulas(monthFormulas);

  // Number formatting
  sheet.getRange(ts + 1, 3, 12, 1).setNumberFormat('0.00%');
  sheet.getRange(ts + 1, 4, 12, 1).setNumberFormat('0%');
  sheet.getRange(ts + 1, 5, 12, 3).setNumberFormat('0.00%');

  sheet.getRange(ts, 1, 13, 7).setBorder(true, true, true, true, true, true);

  // Alternating rows
  for (var r = ts + 1; r <= ts + 12; r++) {
    if (r % 2 === 0) sheet.getRange(r, 1, 1, 7).setBackground('#F2F2F2');
  }

  // Seasonality chart
  createSeasonalityChart_(sheet, ts);
}

function createSeasonalityChart_(sheet, tableStart) {
  var dataRange = sheet.getRange(tableStart, 2, 13, 2);

  var chart = sheet.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(dataRange)
    .setPosition(tableStart - 1, 8, 0, 0)
    .setOption('title', 'Monthly Seasonality - Avg Return %')
    .setOption('legend', { position: 'none' })
    .setOption('hAxis', { title: 'Month' })
    .setOption('vAxis', { title: 'Average Return', format: '0.00%' })
    .setOption('width', 550)
    .setOption('height', 320)
    .setOption('colors', ['#4472C4'])
    .setOption('bar', { groupWidth: '70%' })
    .build();

  sheet.insertChart(chart);
}

// ====================================================================
// CONDITIONAL FORMATTING
// ====================================================================
function applyConditionalFormatting_(sheet) {
  var rules = [];
  var signalRange = sheet.getRange('C5:C10');
  var sectorSignalRange = sheet.getRange('F14:F24');
  var seasonalitySignal = sheet.getRange('B29');

  // Red signals
  var redTerms = ['OVERBOUGHT', 'RED LIGHT', 'WEAK', 'EUPHORIA', 'DIVERGENCE', 'SELLING'];
  for (var i = 0; i < redTerms.length; i++) {
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextContains(redTerms[i])
      .setBackground('#FFC7CE').setFontColor('#9C0006')
      .setRanges([signalRange]).build());
  }

  // Green signals
  var greenTerms = ['OVERSOLD', 'GREEN LIGHT', 'STRONG BULL', 'FEAR', 'HEALTHY', 'BUYING'];
  for (var i = 0; i < greenTerms.length; i++) {
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextContains(greenTerms[i])
      .setBackground('#C6EFCE').setFontColor('#006100')
      .setRanges([signalRange]).build());
  }

  // Yellow signals
  var yellowTerms = ['CAUTION', 'CAUTIOUS', 'NEUTRAL'];
  for (var i = 0; i < yellowTerms.length; i++) {
    rules.push(SpreadsheetApp.newConditionalFormatRule()
      .whenTextContains(yellowTerms[i])
      .setBackground('#FFEB9C').setFontColor('#9C6500')
      .setRanges([signalRange]).build());
  }

  // Sector signals
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains('HOT')
    .setBackground('#C6EFCE').setFontColor('#006100')
    .setRanges([sectorSignalRange]).build());

  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains('COLD')
    .setBackground('#FFC7CE').setFontColor('#9C0006')
    .setRanges([sectorSignalRange]).build());

  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains('NEUTRAL')
    .setBackground('#FFEB9C').setFontColor('#9C6500')
    .setRanges([sectorSignalRange]).build());

  // Seasonality signal
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains('BULLISH')
    .setBackground('#C6EFCE').setFontColor('#006100')
    .setRanges([seasonalitySignal]).build());

  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains('BEARISH')
    .setBackground('#FFC7CE').setFontColor('#9C0006')
    .setRanges([seasonalitySignal]).build());

  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains('FLAT')
    .setBackground('#FFEB9C').setFontColor('#9C6500')
    .setRanges([seasonalitySignal]).build());

  sheet.setConditionalFormatRules(rules);
}
