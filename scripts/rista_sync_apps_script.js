/**
 * Rista POS Analytics - Google Apps Script
 * Auto-syncs daily sales data from Rista POS API
 * Single row per date with all account breakdowns
 *
 * Setup:
 * 1. Create a new Google Sheet
 * 2. Go to Extensions → Apps Script
 * 3. Paste this entire code
 * 4. Save and run onOpen() once to create menu
 * 5. Click "Rista Sync" → "Setup Daily Trigger" (one-time)
 */

// ============================================================
// CONFIGURATION - Your Rista API Credentials
// ============================================================
const CONFIG = {
  API_KEY: '9e0c5790-1ef5-4eb9-b552-7d8e24eef23d',
  API_SECRET: 'N915f-qsLspRfq86x_YVvpFVCD_Wm7aXqKrNFZA8OkY',
  BASE_URL: 'https://api.ristaapps.com/v1',
  BRANCH: 'HYD',
  SHEET_NAME: 'Daily Sales'
  // Accounts are detected dynamically from API - no hardcoding needed!
};

// ============================================================
// MENU SETUP
// ============================================================

/**
 * Creates custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Rista Sync')
    .addItem('Sync Today', 'syncToday')
    .addItem('Sync Yesterday', 'syncYesterday')
    .addItem('Sync Date Range...', 'showDateRangeDialog')
    .addSeparator()
    .addItem('Create Dashboard', 'createDashboard')
    .addItem('Refresh Dashboard', 'refreshDashboard')
    .addSeparator()
    .addItem('Import CSV from Rista...', 'showCsvImportDialog')
    .addSeparator()
    .addItem('Setup Daily Trigger', 'setupDailyTrigger')
    .addItem('Remove Daily Trigger', 'removeDailyTrigger')
    .addSeparator()
    .addItem('Reset Sheet', 'recreateSheet')
    .addToUi();
}

// ============================================================
// JWT AUTHENTICATION (HS256)
// ============================================================

/**
 * Generate JWT token for Rista API authentication
 */
function generateJWT() {
  const header = {
    alg: 'HS256',
    typ: 'JWT'
  };

  const payload = {
    iss: CONFIG.API_KEY,
    iat: Math.floor(Date.now() / 1000),
    jti: Utilities.getUuid()
  };

  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));

  const signatureInput = encodedHeader + '.' + encodedPayload;
  const signature = computeHmacSha256(signatureInput, CONFIG.API_SECRET);

  return signatureInput + '.' + signature;
}

/**
 * Base64 URL encode (JWT-safe)
 */
function base64UrlEncode(str) {
  const base64 = Utilities.base64Encode(str);
  return base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/**
 * Compute HMAC-SHA256 signature
 */
function computeHmacSha256(message, secret) {
  const signature = Utilities.computeHmacSha256Signature(message, secret);
  const base64 = Utilities.base64Encode(signature);
  return base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

// ============================================================
// RISTA API CLIENT
// ============================================================

/**
 * Make authenticated API request
 */
function apiRequest(endpoint, params) {
  const token = generateJWT();

  let url = CONFIG.BASE_URL + endpoint;
  if (params) {
    const queryString = Object.entries(params)
      .map(([k, v]) => encodeURIComponent(k) + '=' + encodeURIComponent(v))
      .join('&');
    url += '?' + queryString;
  }

  const options = {
    method: 'GET',
    headers: {
      'x-api-key': CONFIG.API_KEY,
      'x-api-token': token,
      'Content-Type': 'application/json'
    },
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  return {
    status: response.getResponseCode(),
    data: response.getResponseCode() === 200 ? JSON.parse(response.getContentText()) : null,
    error: response.getResponseCode() !== 200 ? response.getContentText() : null
  };
}

/**
 * Fetch Sales By Item data and aggregate by Account Name
 * @param {string} date - Date in YYYY-MM-DD format
 * @returns {Object} Aggregated data with accounts breakdown
 */
function fetchSalesSummary(date) {
  // Try Sales By Item endpoint first (has Account Name)
  const itemsResult = apiRequest('/analytics/sales/items', {
    branch: CONFIG.BRANCH,
    period: date
  });

  if (itemsResult.status === 200 && itemsResult.data) {
    return aggregateByAccount(itemsResult.data);
  }

  // Try alternate endpoint names
  const altEndpoints = [
    '/analytics/sales/by-item',
    '/reports/sales/items',
    '/analytics/item/summary'
  ];

  for (const endpoint of altEndpoints) {
    const result = apiRequest(endpoint, { branch: CONFIG.BRANCH, period: date });
    if (result.status === 200 && result.data) {
      return aggregateByAccount(result.data);
    }
  }

  // Fall back to standard analytics summary
  const summaryResult = apiRequest('/analytics/sales/summary', {
    branch: CONFIG.BRANCH,
    period: date
  });

  if (summaryResult.status !== 200) {
    throw new Error('API Error: ' + summaryResult.status + ' - ' + summaryResult.error);
  }

  return summaryResult.data;
}

/**
 * Aggregate item-level data by Account Name
 * Cleans account names to remove COGS suffixes and invalid entries
 */
function aggregateByAccount(data) {
  // Handle different response structures
  const items = data.items || data.sales || data.records || (Array.isArray(data) ? data : []);

  if (items.length === 0) {
    return data;  // Return as-is if no items
  }

  // Aggregate by Account Name (cleaned)
  const accountTotals = {};
  let totalNet = 0;
  let totalCost = 0;

  for (const item of items) {
    const rawAccountName = item.accountName || item['Account Name'] || item.account || '';
    const accountName = cleanAccountName(rawAccountName);

    // Handle various field name formats for Net Amount
    const netAmount = parseFloat(
      item['Net Amount'] || item.netAmount || item['net amount'] ||
      item.NetAmount || item.net_amount || item.amount || item.Amount || 0
    );

    // Handle various field name formats for Materials Cost (CSV uses "Materials Cost")
    const materialCost = parseFloat(
      item['Materials Cost'] || item.materialsCost || item['materials cost'] ||
      item.MaterialsCost || item.materials_cost || item['Material Cost'] ||
      item.materialCost || item.material_cost || item.costOfGoodsSold ||
      item['Cost of Goods Sold'] || item.cost || item.Cost || item.COGS || 0
    );

    totalNet += netAmount;
    totalCost += materialCost;

    if (accountName) {
      if (!accountTotals[accountName]) {
        accountTotals[accountName] = { net: 0, cost: 0 };
      }
      accountTotals[accountName].net += netAmount;
      accountTotals[accountName].cost += materialCost;
    }
  }

  // Build accounts array
  const accounts = Object.entries(accountTotals).map(([name, totals]) => ({
    name: name,
    netAmount: totals.net,
    costOfGoodsSold: totals.cost
  }));

  return {
    netAmount: totalNet,
    costOfGoodsSold: totalCost,
    accounts: accounts
  };
}

// ============================================================
// SYNC FUNCTIONS
// ============================================================

/**
 * Sync today's data
 */
function syncToday() {
  const today = formatDate(new Date());
  syncDate(today);
  SpreadsheetApp.getUi().alert('Synced data for ' + today);
}

/**
 * Sync yesterday's data (used by daily trigger)
 */
function syncYesterday() {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const dateStr = formatDate(yesterday);
  syncDate(dateStr);
  Logger.log('Synced data for ' + dateStr);
}

/**
 * Sync data for a specific date
 * @param {string} date - Date in YYYY-MM-DD format
 */
function syncDate(date) {
  const sheet = getOrCreateSheet();

  // Check if date already exists
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
      var cellVal = data[i][0] instanceof Date ? formatDate(data[i][0]) : String(data[i][0]);
            if (cellVal === date) {
      // Update existing row
      updateRow(sheet, i + 1, date);
      return;
    }
  }

  // Add new row
  addRow(sheet, date);
}

/**
 * Sync a range of dates
 */
function syncDateRange(startDate, endDate) {
  const start = new Date(startDate);
  const end = new Date(endDate);

  const current = new Date(start);
  let count = 0;

  while (current <= end) {
    try {
      syncDate(formatDate(current));
      count++;
    } catch (e) {
      Logger.log('Error syncing ' + formatDate(current) + ': ' + e.message);
    }
    current.setDate(current.getDate() + 1);
  }

  return count;
}

/**
 * Show date range picker dialog
 */
function showDateRangeDialog() {
  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 15px; }
      label { display: block; margin-top: 10px; }
      input { padding: 8px; width: 100%; box-sizing: border-box; }
      button { margin-top: 15px; padding: 10px 20px; background: #4285f4; color: white; border: none; cursor: pointer; }
      button:hover { background: #357abd; }
    </style>
    <label>Start Date:</label>
    <input type="date" id="startDate">
    <label>End Date:</label>
    <input type="date" id="endDate">
    <button onclick="sync()">Sync Range</button>
    <script>
      function sync() {
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        if (!start || !end) {
          alert('Please select both dates');
          return;
        }
        google.script.run
          .withSuccessHandler(function(count) {
            alert('Synced ' + count + ' days');
            google.script.host.close();
          })
          .withFailureHandler(function(e) {
            alert('Error: ' + e.message);
          })
          .syncDateRange(start, end);
      }
    </script>
  `)
  .setWidth(300)
  .setHeight(200);

  SpreadsheetApp.getUi().showModalDialog(html, 'Sync Date Range');
}

// ============================================================
// SHEET OPERATIONS
// ============================================================

// Base headers (always present)
const BASE_HEADERS = ['Date', 'Total Net', 'Total Cost', 'Total Profit', 'Total Margin %'];

/**
 * Get or create the Daily Sales sheet with headers
 */
function getOrCreateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
    setupBaseHeaders(sheet);
  }

  return sheet;
}

/**
 * Setup sheet with base headers and formatting
 */
function setupBaseHeaders(sheet) {
  sheet.getRange(1, 1, 1, BASE_HEADERS.length).setValues([BASE_HEADERS]);

  // Format header row
  sheet.getRange(1, 1, 1, BASE_HEADERS.length)
    .setFontWeight('bold')
    .setBackground('#4285f4')
    .setFontColor('white')
    .setWrap(true);

  // Set column widths
  sheet.setColumnWidth(1, 100);  // Date
  for (let i = 2; i <= 5; i++) {
    sheet.setColumnWidth(i, 100);
  }

  // Format currency columns
  sheet.getRange(2, 2, 1000, 3).setNumberFormat('\u20B9#,##0');
  sheet.getRange(2, 5, 1000, 1).setNumberFormat('0.0%');

  // Freeze header row and date column
  sheet.setFrozenRows(1);
  sheet.setFrozenColumns(1);
}

/**
 * Get existing account names from sheet headers
 */
function getExistingAccounts(sheet) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const accounts = [];

  for (let i = BASE_HEADERS.length; i < headers.length; i += 3) {
    const header = headers[i] || '';
    // Extract account name from "Account Net" header
    if (header.endsWith(' Net')) {
      accounts.push(header.replace(' Net', ''));
    }
  }

  return accounts;
}

/**
 * Add new account columns to sheet
 */
function addAccountColumns(sheet, accountName) {
  const lastCol = sheet.getLastColumn();
  const newHeaders = [accountName + ' Net', accountName + ' Cost', accountName + ' Profit'];

  // Add headers
  sheet.getRange(1, lastCol + 1, 1, 3).setValues([newHeaders]);

  // Format new header columns
  sheet.getRange(1, lastCol + 1, 1, 3)
    .setFontWeight('bold')
    .setBackground('#4285f4')
    .setFontColor('white')
    .setWrap(true);

  // Set column widths
  for (let i = 0; i < 3; i++) {
    sheet.setColumnWidth(lastCol + 1 + i, 90);
  }

  // Format as currency
  sheet.getRange(2, lastCol + 1, 1000, 3).setNumberFormat('\u20B9#,##0');

  Logger.log('Added new account columns: ' + accountName);
}

/**
 * Clean account name - remove COGS suffixes and invalid entries
 */
function cleanAccountName(name) {
  if (!name) return '';

  // Skip if it contains COGS, %, or other metric suffixes
  if (name.includes('-COGS') || name.includes('COGS%') || name.includes('%')) {
    return '';
  }

  // Skip generic/metric names
  const skipNames = ['COGS', 'Net', 'Gross', 'Profit', 'Margin', 'Total', 'Amount'];
  for (const skip of skipNames) {
    if (name === skip || name.endsWith(' ' + skip)) {
      return '';
    }
  }

  return name.trim();
}

/**
 * Get account names from API response
 */
function getApiAccounts(apiData) {
  const accounts = [];

  // Get from accounts array (our aggregated data)
  const accountList = apiData.accounts || [];
  for (const acc of accountList) {
    const rawName = acc.name || acc.accountName || '';
    const name = cleanAccountName(rawName);
    if (name && !accounts.includes(name)) {
      accounts.push(name);
    }
  }

  // Also check categories as fallback - but only use accountName field
  if (accounts.length === 0) {
    const categories = apiData.categories || [];
    for (const cat of categories) {
      // Only use accountName, not category name
      const rawName = cat.accountName || cat.account || '';
      const name = cleanAccountName(rawName);
      if (name && !accounts.includes(name)) {
        accounts.push(name);
      }
    }
  }

  return accounts.sort();  // Sort alphabetically for consistency
}

/**
 * Ensure all accounts from API have columns in sheet
 */
function ensureAccountColumns(sheet, apiData) {
  const existingAccounts = getExistingAccounts(sheet);
  const apiAccounts = getApiAccounts(apiData);

  // Add columns for any new accounts
  for (const account of apiAccounts) {
    if (!existingAccounts.includes(account)) {
      addAccountColumns(sheet, account);
      existingAccounts.push(account);  // Update local list
    }
  }

  return existingAccounts;
}

/**
 * Build row data from API response (dynamic based on sheet headers)
 */
function buildRowData(sheet, date, apiData) {
  const netAmount = parseFloat(apiData.netAmount || 0);
  const materialCost = parseFloat(apiData.costOfGoodsSold || 0);
  const profit = netAmount - materialCost;
  const margin = netAmount > 0 ? profit / netAmount : 0;

  // Start with totals
  const row = [date, netAmount, materialCost, profit, margin];

  // Build account data map
  const accountMap = buildAccountDataMap(apiData);

  // Get accounts from sheet headers (in order)
  const accounts = getExistingAccounts(sheet);

  // Add each account's data in header order
  for (const account of accounts) {
    const accountData = accountMap[account] || { net: 0, cost: 0 };
    const accountProfit = accountData.net - accountData.cost;

    row.push(accountData.net);
    row.push(accountData.cost);
    row.push(accountProfit);
  }

  return row;
}

/**
 * Build account data map from API response
 * Uses cleanAccountName() to ensure keys match column headers
 */
function buildAccountDataMap(apiData) {
  const accountMap = {};

  // Get from accounts array (our aggregated data)
  const accounts = apiData.accounts || [];
  for (const acc of accounts) {
    const rawName = acc.name || acc.accountName || '';
    const name = cleanAccountName(rawName);
    if (name) {
      // Aggregate in case multiple raw names clean to the same name
      if (!accountMap[name]) {
        accountMap[name] = { net: 0, cost: 0 };
      }
      // Net amount
      accountMap[name].net += parseFloat(
        acc.netAmount || acc['Net Amount'] || acc.amount || acc.Amount || 0
      );
      // Materials Cost (comprehensive field name check)
      accountMap[name].cost += parseFloat(
        acc['Materials Cost'] || acc.materialsCost || acc.costOfGoodsSold ||
        acc['Cost of Goods Sold'] || acc.MaterialsCost || acc.materials_cost ||
        acc.cost || acc.Cost || 0
      );
    }
  }

  // Fallback to categories if no accounts
  if (Object.keys(accountMap).length === 0) {
    const categories = apiData.categories || [];
    for (const cat of categories) {
      const rawName = cat.accountName || cat.account || '';
      const name = cleanAccountName(rawName);
      if (name) {
        if (!accountMap[name]) {
          accountMap[name] = { net: 0, cost: 0 };
        }
        accountMap[name].net += parseFloat(
          cat.netAmount || cat['Net Amount'] || cat.amount || 0
        );
        accountMap[name].cost += parseFloat(
          cat['Materials Cost'] || cat.materialsCost || cat.costOfGoodsSold ||
          cat['Cost of Goods Sold'] || cat.cost || 0
        );
      }
    }
  }

  return accountMap;
}

/**
 * Add new row with sales data
 */
function addRow(sheet, date) {
  const apiData = fetchSalesSummary(date);

  // Ensure all accounts from API have columns
  ensureAccountColumns(sheet, apiData);

  const row = buildRowData(sheet, date, apiData);
  sheet.appendRow(row);

  // Sort by date descending (newest first)
  const lastRow = sheet.getLastRow();
  const numCols = sheet.getLastColumn();
  if (lastRow > 2) {
    sheet.getRange(2, 1, lastRow - 1, numCols).sort({column: 1, ascending: false});
  }
}

/**
 * Update existing row with new data
 */
function updateRow(sheet, rowIndex, date) {
  const apiData = fetchSalesSummary(date);

  // Ensure all accounts from API have columns
  ensureAccountColumns(sheet, apiData);

  const row = buildRowData(sheet, date, apiData);

  // Update all columns (expand range if needed)
  const numCols = sheet.getLastColumn();
  sheet.getRange(rowIndex, 1, 1, numCols).setValues([row.concat(Array(numCols - row.length).fill(''))]);
}

/**
 * Recreate sheet (clears all data and headers)
 */
function recreateSheet() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Recreate Sheet',
    'This will delete all data and start fresh. Continue?',
    ui.ButtonSet.YES_NO
  );

  if (response === ui.Button.YES) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const existingSheet = ss.getSheetByName(CONFIG.SHEET_NAME);

    if (existingSheet) {
      ss.deleteSheet(existingSheet);
    }

    const newSheet = ss.insertSheet(CONFIG.SHEET_NAME);
    setupBaseHeaders(newSheet);

    ui.alert('Sheet recreated. Sync data to populate - account columns will be added automatically.');
  }
}

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return year + '-' + month + '-' + day;
}

// ============================================================
// TRIGGER MANAGEMENT
// ============================================================

/**
 * Set up daily trigger to run at 5 PM EST
 */
function setupDailyTrigger() {
  // Remove any existing triggers first
  removeDailyTrigger();

  // Create new trigger for 5 PM (17:00) daily
  // Note: Ensure script timezone is set to EST in Project Settings
  ScriptApp.newTrigger('syncYesterday')
    .timeBased()
    .atHour(17)
    .everyDays(1)
    .inTimezone('America/New_York')
    .create();

  SpreadsheetApp.getUi().alert('Daily sync trigger set up! Will run every day at 5 PM EST.');
}

/**
 * Remove daily trigger
 */
function removeDailyTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'syncYesterday') {
      ScriptApp.deleteTrigger(trigger);
    }
  }
}

// ============================================================
// TESTING
// ============================================================

/**
 * Test API connection and show detected accounts
 */
function testConnection() {
  try {
    const today = formatDate(new Date());
    const data = fetchSalesSummary(today);
    const accounts = getApiAccounts(data);

    Logger.log('=== API Connection Successful ===');
    Logger.log('Net Amount: \u20B9' + data.netAmount);
    Logger.log('Material Cost: \u20B9' + data.costOfGoodsSold);
    Logger.log('');
    Logger.log('=== Detected Accounts ===');
    for (const account of accounts) {
      Logger.log('  - ' + account);
    }
    Logger.log('');
    Logger.log('These accounts will automatically get columns when you sync.');

    return true;
  } catch (e) {
    Logger.log('API Connection failed: ' + e.message);
    return false;
  }
}

/**
 * Debug: Log full API response and show available fields
 */
function debugApiResponse() {
  const today = formatDate(new Date());
  const data = fetchSalesSummary(today);

  Logger.log('=== Full API Response ===');
  Logger.log(JSON.stringify(data, null, 2));

  Logger.log('');
  Logger.log('=== Top-level fields ===');
  for (const key of Object.keys(data)) {
    Logger.log('  - ' + key + ': ' + typeof data[key]);
  }

  // Check for accounts field
  if (data.accounts) {
    Logger.log('');
    Logger.log('=== Accounts field found ===');
    Logger.log(JSON.stringify(data.accounts, null, 2));
  }

  // Check categories structure
  if (data.categories && data.categories.length > 0) {
    Logger.log('');
    Logger.log('=== First category fields ===');
    const firstCat = data.categories[0];
    for (const key of Object.keys(firstCat)) {
      Logger.log('  - ' + key + ': ' + firstCat[key]);
    }
  }
}

/**
 * Show currently tracked accounts
 */
function showTrackedAccounts() {
  const sheet = getOrCreateSheet();
  const accounts = getExistingAccounts(sheet);

  if (accounts.length === 0) {
    SpreadsheetApp.getUi().alert('No accounts tracked yet. Sync some data first!');
  } else {
    SpreadsheetApp.getUi().alert('Currently tracked accounts:\n\n\u2022 ' + accounts.join('\n\u2022 '));
  }
}

/**
 * Show API response in a dialog for debugging
 */
function showApiDebug() {
  const today = formatDate(new Date());
  let message = '';

  try {
    // Try multiple endpoints to find item-level data
    const endpoints = [
      '/analytics/sales/items',
      '/analytics/item/sales',
      '/reports/sales/items',
      '/analytics/sales/by-item',
      '/reports/item-sales'
    ];

    message = '=== Searching for Item Data (' + today + ') ===\n\n';

    for (const endpoint of endpoints) {
      const result = apiRequest(endpoint, {
        branch: CONFIG.BRANCH,
        period: today
      });

      message += endpoint + ': ' + result.status + '\n';

      if (result.status === 200 && result.data) {
        const rawData = result.data;

        // Get items array
        const items = rawData.items || rawData.sales || rawData.records || (Array.isArray(rawData) ? rawData : []);

        if (items.length > 0) {
          message += '  \u2713 Found ' + items.length + ' items!\n';
          message += '  Fields: ' + Object.keys(items[0]).join(', ') + '\n';

          // Check for Materials Cost field
          const firstItem = items[0];
          const hasMaterialsCost = 'Materials Cost' in firstItem ||
                                   'materialsCost' in firstItem ||
                                   'MaterialsCost' in firstItem;
          const hasAccountName = 'Account Name' in firstItem ||
                                 'accountName' in firstItem;

          message += '  Has Materials Cost: ' + (hasMaterialsCost ? 'YES' : 'NO') + '\n';
          message += '  Has Account Name: ' + (hasAccountName ? 'YES' : 'NO') + '\n';

          // Show first item details
          message += '\n  First Item:\n';
          message += '  ' + JSON.stringify(firstItem, null, 2).substring(0, 400).replace(/\n/g, '\n  ') + '\n';

          // Log full response
          Logger.log('Found data at ' + endpoint + ':');
          Logger.log(JSON.stringify(rawData, null, 2));

          break;  // Found working endpoint
        } else {
          message += '  (no items array)\n';
        }
      }
      message += '\n';
    }

    message += '(Full response logged to View > Logs)';

  } catch (e) {
    message = 'Error: ' + e.message;
    Logger.log('Debug error: ' + e.message);
  }

  SpreadsheetApp.getUi().alert(message);
}

/**
 * Debug: Show aggregated data (what gets written to sheet)
 */
function showAggregatedDebug() {
  const today = formatDate(new Date());
  let message = '';

  try {
    const data = fetchSalesSummary(today);

    message = '=== Aggregated Data for ' + today + ' ===\n\n';
    message += 'Total Net: \u20B9' + (data.netAmount || 0).toLocaleString() + '\n';
    message += 'Total Cost: \u20B9' + (data.costOfGoodsSold || 0).toLocaleString() + '\n';
    message += 'Total Profit: \u20B9' + ((data.netAmount || 0) - (data.costOfGoodsSold || 0)).toLocaleString() + '\n\n';

    const accounts = data.accounts || [];
    if (accounts.length > 0) {
      message += '=== By Account (' + accounts.length + ') ===\n\n';
      for (const acc of accounts) {
        const net = acc.netAmount || 0;
        const cost = acc.costOfGoodsSold || 0;
        const profit = net - cost;
        message += '\u2022 ' + acc.name + '\n';
        message += '  Net: \u20B9' + net.toLocaleString() + '\n';
        message += '  Cost: \u20B9' + cost.toLocaleString() + '\n';
        message += '  Profit: \u20B9' + profit.toLocaleString() + '\n\n';
      }
    } else {
      message += 'No account breakdown available.\n';
    }

    Logger.log('Aggregated data:');
    Logger.log(JSON.stringify(data, null, 2));

  } catch (e) {
    message = 'Error: ' + e.message;
    Logger.log('Debug error: ' + e.message);
  }

  SpreadsheetApp.getUi().alert(message);
}

// ============================================================
// CSV IMPORT (for Account Name breakdown)
// ============================================================

/**
 * Show dialog for CSV import
 */
function showCsvImportDialog() {
  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h3 { margin-top: 0; color: #333; }
      .info { background: #e3f2fd; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 13px; }
      label { display: block; margin-top: 15px; font-weight: bold; }
      input[type="date"] { padding: 8px; width: 100%; box-sizing: border-box; margin-top: 5px; }
      textarea { width: 100%; height: 150px; margin-top: 5px; font-family: monospace; font-size: 11px; }
      button { margin-top: 15px; padding: 12px 24px; background: #4285f4; color: white; border: none; cursor: pointer; font-size: 14px; }
      button:hover { background: #357abd; }
      .steps { font-size: 12px; color: #666; margin-top: 10px; }
      .steps ol { margin: 5px 0; padding-left: 20px; }
    </style>
    <h3>Import Sales By Items CSV</h3>
    <div class="info">
      Since the API doesn't provide Account Name breakdown, you can import the CSV exported from Rista.
    </div>
    <div class="steps">
      <strong>Steps:</strong>
      <ol>
        <li>In Rista, go to Reports \u2192 Sales By Items</li>
        <li>Select the date and export as CSV</li>
        <li>Open the CSV file and copy ALL contents (Ctrl+A, Ctrl+C)</li>
        <li>Paste below and click Import</li>
      </ol>
    </div>
    <label>Date for this data:</label>
    <input type="date" id="csvDate">
    <label>Paste CSV contents:</label>
    <textarea id="csvData" placeholder="Paste CSV data here..."></textarea>
    <button onclick="importCsv()">Import CSV</button>
    <script>
      // Set default date to today
      document.getElementById('csvDate').valueAsDate = new Date();

      function importCsv() {
        const date = document.getElementById('csvDate').value;
        const csvData = document.getElementById('csvData').value;
        if (!date) {
          alert('Please select a date');
          return;
        }
        if (!csvData.trim()) {
          alert('Please paste CSV data');
          return;
        }
        google.script.run
          .withSuccessHandler(function(result) {
            alert(result);
            google.script.host.close();
          })
          .withFailureHandler(function(e) {
            alert('Error: ' + e.message);
          })
          .importCsvData(date, csvData);
      }
    </script>
  `)
  .setWidth(500)
  .setHeight(480);

  SpreadsheetApp.getUi().showModalDialog(html, 'Import CSV');
}

/**
 * Import CSV data and aggregate by Account Name
 * @param {string} date - Date in YYYY-MM-DD format
 * @param {string} csvData - Raw CSV content
 */
function importCsvData(date, csvData) {
  const lines = csvData.split('\n');

  // Find header row (skip the first row which is a title)
  let headerIndex = -1;
  let headers = [];

  for (let i = 0; i < Math.min(5, lines.length); i++) {
    const line = lines[i];
    if (line.includes('Account Name') || line.includes('Net Amount') || line.includes('SKU')) {
      headers = parseCsvLine(line);
      headerIndex = i;
      break;
    }
  }

  if (headerIndex === -1) {
    throw new Error('Could not find header row. Make sure CSV contains "Account Name" column.');
  }

  // Find column indices
  const accountNameIdx = findColumnIndex(headers, ['Account Name', 'accountName']);
  const netAmountIdx = findColumnIndex(headers, ['Net Amount', 'netAmount', 'Net']);
  const materialsCostIdx = findColumnIndex(headers, ['Materials Cost', 'materialsCost', 'Material Cost']);

  if (accountNameIdx === -1) {
    throw new Error('Could not find "Account Name" column in CSV');
  }
  if (netAmountIdx === -1) {
    throw new Error('Could not find "Net Amount" column in CSV');
  }

  // Aggregate by Account Name
  const accountTotals = {};
  let totalNet = 0;
  let totalCost = 0;
  let rowCount = 0;

  for (let i = headerIndex + 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const values = parseCsvLine(line);
    if (values.length <= accountNameIdx) continue;

    const accountName = cleanAccountName(values[accountNameIdx] || '');
    const netAmount = parseNumber(values[netAmountIdx]);
    const materialsCost = materialsCostIdx >= 0 ? parseNumber(values[materialsCostIdx]) : 0;

    if (!accountName) continue;

    totalNet += netAmount;
    totalCost += materialsCost;
    rowCount++;

    if (!accountTotals[accountName]) {
      accountTotals[accountName] = { net: 0, cost: 0 };
    }
    accountTotals[accountName].net += netAmount;
    accountTotals[accountName].cost += materialsCost;
  }

  if (rowCount === 0) {
    throw new Error('No data rows found in CSV');
  }

  // Build accounts array
  const accounts = Object.entries(accountTotals).map(([name, totals]) => ({
    name: name,
    netAmount: totals.net,
    costOfGoodsSold: totals.cost
  }));

  // Create API-like data structure
  const apiData = {
    netAmount: totalNet,
    costOfGoodsSold: totalCost,
    accounts: accounts
  };

  // Write to sheet
  const sheet = getOrCreateSheet();

  // Check if date already exists
  const data = sheet.getDataRange().getValues();
  let rowIndex = -1;
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === date) {
      rowIndex = i + 1;
      break;
    }
  }

  // Ensure account columns exist
  ensureAccountColumns(sheet, apiData);

  // Build and write row
  const row = buildRowData(sheet, date, apiData);

  if (rowIndex > 0) {
    // Update existing row
    const numCols = sheet.getLastColumn();
    sheet.getRange(rowIndex, 1, 1, numCols).setValues([row.concat(Array(numCols - row.length).fill(''))]);
  } else {
    // Add new row
    sheet.appendRow(row);

    // Sort by date descending
    const lastRow = sheet.getLastRow();
    const numCols = sheet.getLastColumn();
    if (lastRow > 2) {
      sheet.getRange(2, 1, lastRow - 1, numCols).sort({column: 1, ascending: false});
    }
  }

  return 'Imported ' + rowCount + ' items for ' + date + '\n\n' +
         'Totals:\n' +
         '\u2022 Net Amount: \u20B9' + totalNet.toLocaleString() + '\n' +
         '\u2022 Materials Cost: \u20B9' + totalCost.toLocaleString() + '\n' +
         '\u2022 Profit: \u20B9' + (totalNet - totalCost).toLocaleString() + '\n\n' +
         'Accounts: ' + accounts.map(a => a.name).join(', ');
}

/**
 * Parse a CSV line handling quoted values
 */
function parseCsvLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current.trim());

  return values;
}

/**
 * Find column index from possible header names
 */
function findColumnIndex(headers, possibleNames) {
  for (let i = 0; i < headers.length; i++) {
    const header = headers[i].replace(/"/g, '').trim();
    for (const name of possibleNames) {
      if (header.toLowerCase() === name.toLowerCase()) {
        return i;
      }
    }
  }
  return -1;
}

/**
 * Parse number from string (handles currency symbols, commas)
 */
function parseNumber(str) {
  if (!str) return 0;
  // Remove quotes, currency symbols, commas
  const cleaned = String(str).replace(/[",\u20B9$]/g, '').trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

// ============================================================
// DASHBOARD & METRICS (for Google Sites)
// ============================================================

/**
 * Create or update the Dashboard sheet with KPIs and charts
 */
function createDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dataSheet = ss.getSheetByName(CONFIG.SHEET_NAME);

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('No data found. Please sync some data first.');
    return;
  }

  // Delete existing dashboard if present
  let dashboard = ss.getSheetByName('Dashboard');
  if (dashboard) {
    ss.deleteSheet(dashboard);
  }

  // Create new dashboard
  dashboard = ss.insertSheet('Dashboard');

  // Set up the dashboard layout
  setupDashboardKPIs(dashboard);

  // Force all formulas to calculate before creating charts
  SpreadsheetApp.flush();

  // Small delay to ensure formulas are fully calculated
  Utilities.sleep(2000);

  setupDashboardCharts(dashboard);

  // Move dashboard to first position
  ss.setActiveSheet(dashboard);
  ss.moveActiveSheet(1);

  SpreadsheetApp.getUi().alert('Dashboard created!');
}

/**
 * Refresh dashboard data
 */
function refreshDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboard = ss.getSheetByName('Dashboard');

  if (!dashboard) {
    createDashboard();
    return;
  }

  // Force recalculation by touching the timestamp
  dashboard.getRange('B2').setValue(new Date());

  SpreadsheetApp.getUi().alert('Dashboard refreshed!');
}
