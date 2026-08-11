const translations = {
  en: {
    "home.title": "TradeAI",
    "home.subtitle": "A focused forex dashboard with live prices, indicators, charts, and AI analysis.",
    "home.feature1": "Calculate RSI and MACD without heavy system dependencies.",
    "home.feature2": "Fetch live market data with a TwelveData API key or Yahoo fallback.",
    "home.feature3": "Generate professional text analysis with your OpenAI API key.",
    "home.feature4": "View charts, indicators, and a decision summary in one place.",
    "home.login": "Sign in",
    "home.start": "Start free analysis",
    "login.title": "Sign in",
    "login.subtitle": "Sign in to access the analysis dashboard.",
    "login.error": "Invalid username or password.",
    "login.username": "Username",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.back": "Back to home",
    "dashboard.logout": "Logout",
    "dashboard.eyebrow": "Forex intelligence workspace",
    "dashboard.title": "Forex Analysis Dashboard",
    "dashboard.user": "User",
    "session.label": "Market session",
    "mt5.eyebrow": "Local demo connection",
    "mt5.title": "MetaTrader 5",
    "mt5.disconnected": "Disconnected",
    "mt5.checking": "Checking connection…",
    "mt5.connected": "Demo connected",
    "mt5.account": "Account",
    "mt5.server": "Server",
    "mt5.balance": "Balance",
    "mt5.equity": "Equity",
    "mt5.margin": "Margin",
    "mt5.mode": "Execution mode",
    "mt5.connect": "Check connection",
    "mt5.fetch": "Load candles from MT5",
    "mt5.minStrength": "Minimum strength",
    "mt5.maxSpread": "Maximum spread (bps)",
    "mt5.riskPercent": "Risk per signal (%)",
    "mt5.maxVolume": "Maximum volume (lot)",
    "mt5.atrStop": "ATR stop multiple",
    "mt5.rewardRisk": "Reward/Risk",
    "mt5.preview": "Build safe signal preview",
    "mt5.safety": "Safe mode is active: no order can be sent. The current incomplete candle is excluded.",
    "mt5.loginRequired": "Sign in to connect the local MetaTrader 5 terminal.",
    "mt5.login": "Sign in",
    "live.title": "Live price feed",
    "live.symbol": "Symbol (example: EUR/USD)",
    "live.interval": "Timeframe",
    "live.outputsize": "Candle count",
    "live.fetch": "Fetch live data",
    "manual.title": "Manual data",
    "manual.prices": "Closing prices (comma separated)",
    "ind.useRsi": "Use RSI",
    "ind.rsiPeriod": "RSI sensitivity",
    "ind.useMacd": "Use MACD",
    "ind.macdShortPeriod": "Fast trend check",
    "ind.macdLong": "Enable MACD long period",
    "ind.macdLongPeriod": "Slow trend check",
    "ind.macdSignal": "Enable MACD signal period",
    "ind.macdSignalPeriod": "Signal smoothing",
    "ind.tdigm": "Enable TDIGM",
    "ind.tdigmValue": "Extra confidence",
    "tip.rsiPeriod": "How many recent candles RSI uses. Lower reacts faster; higher is smoother.",
    "tip.macdShortPeriod": "The fast moving average in MACD. Lower reacts faster to price changes.",
    "tip.macdLongPeriod": "The slower moving average in MACD. Higher focuses on the bigger trend.",
    "tip.macdSignalPeriod": "Smooths the MACD line so crosses are easier to read.",
    "tip.tdigmValue": "Adds a small confidence boost when your own TDIGM condition is active.",
    "ind.calculate": "Calculate indicators",
    "strategy.title": "Strategy preset",
    "strategy.scalp": "Scalp",
    "strategy.scalpNote": "Fast signals for short holds.",
    "strategy.day": "Day trade",
    "strategy.dayNote": "Balanced intraday settings.",
    "strategy.swing": "Swing",
    "strategy.swingNote": "Smoother signals for longer moves.",
    "strategy.goldDemo": "Gold H4 · demo research",
    "strategy.goldDemoNote": "AI-confirmed H1/H4/D1 setup with manual DEMO execution.",
    "setup.label": "Trading setup",
    "setup.emptyTitle": "Waiting for calculation",
    "setup.emptyBadge": "No signal",
    "setup.emptyReason": "Calculate indicators to see the market setup.",
    "setup.explain": "Explain setup",
    "setup.strength": "Signal strength",
    "tradePlan.title": "Trade plan",
    "tradePlan.entry": "Entry area",
    "tradePlan.stop": "Stop loss",
    "tradePlan.target": "Take profit",
    "tradePlan.rr": "Reward/Risk",
    "tradePlan.empty": "Calculate indicators to build an estimated plan.",
    "risk.title": "Risk calculator",
    "risk.balance": "Account balance",
    "risk.percent": "Risk per trade (%)",
    "risk.stopPips": "Stop distance (pips)",
    "risk.pipValue": "Pip value per 1 lot",
    "risk.result": "Suggested position size",
    "decision.title": "Decision panel",
    "decision.price": "Latest price",
    "decision.rsi": "Latest RSI",
    "decision.rsiState": "RSI state",
    "decision.macdBias": "MACD bias",
    "decision.cross": "MACD cross",
    "decision.action": "System suggestion",
    "decision.confidence": "Indicator agreement",
    "decision.risk": "Risk",
    "backtest.title": "Strategy backtest",
    "backtest.note": "Uses only information available at each historical entry. Results include estimated round-trip fees.",
    "backtest.run": "Run backtest",
    "backtest.holding": "Holding bars",
    "backtest.fee": "Fee/spread per side (bps)",
    "backtest.trades": "Trades",
    "backtest.winRate": "Win rate",
    "backtest.totalReturn": "Total return",
    "backtest.profitFactor": "Profit factor",
    "backtest.expectancy": "Expectancy per trade",
    "backtest.drawdown": "Maximum drawdown",
    "backtest.sharpe": "Sharpe (trade-based)",
    "backtest.needData": "At least 50 valid prices are required for backtesting.",
    "backtest.failed": "Backtest failed.",
    "backtest.connection": "Could not connect to the backtest service.",
    "backtest.warning": "Historical performance does not guarantee future results.",
    "backtest.noTrades": "No historical setup matched the selected rule.",
    "history.title": "Analysis and automated decisions",
    "history.refresh": "Refresh",
    "journal.title": "Trading journal",
    "journal.save": "Save entry",
    "journal.buy": "Buy",
    "journal.sell": "Sell",
    "journal.entry": "Entry price",
    "journal.stop": "Stop loss",
    "journal.target": "Take profit",
    "journal.exit": "Exit price (optional)",
    "journal.open": "Open",
    "journal.won": "Won",
    "journal.lost": "Lost",
    "journal.cancelled": "Cancelled",
    "journal.notes": "Notes",
    "mentor.role": "Trading mentor and advisor",
    "mentor.name": "Ostad Kavosh",
    "mentor.available": "Available",
    "mentor.welcome": "I help you understand the analysis, check risk, and review your trade plan. Start by fetching market data.",
    "mentor.education": "Teach me",
    "mentor.advice": "Advise me",
    "mentor.review": "Review my trade",
    "mentor.educationSeed": "Teach me what the current indicators mean and how I should read them.",
    "mentor.adviceSeed": "Advise me about the current setup, focusing on risk and reasons to wait.",
    "mentor.reviewSeed": "Review my current trade plan, entry, stop-loss, target, and position risk.",
    "ai.title": "OpenAI smart analysis",
    "ai.profile": "Trading profile",
    "ai.scalp": "Scalp (very fast short-term)",
    "ai.day": "Day (intraday)",
    "ai.swing": "Swing (hours to days)",
    "ai.nds": "NDS (fast multi-condition confirmation)",
    "ai.holding": "Maximum holding time (minutes - adjustable for every profile)",
    "ai.analyze": "Run smart analysis",
  },
  fa: {
    "home.title": "TradeAI",
    "home.subtitle": "داشبورد متمرکز فارکس با قیمت زنده، اندیکاتور، نمودار و تحلیل هوشمند.",
    "home.feature1": "محاسبه RSI و MACD بدون وابستگی‌های سنگین.",
    "home.feature2": "دریافت داده بازار با TwelveData یا Yahoo.",
    "home.feature3": "تولید تحلیل حرفه‌ای با کلید OpenAI شما.",
    "home.feature4": "مشاهده نمودارها، اندیکاتورها و جمع‌بندی تصمیم در یک صفحه.",
    "home.login": "ورود",
    "home.start": "شروع تحلیل رایگان",
    "login.title": "ورود",
    "login.subtitle": "برای دسترسی به داشبورد تحلیل وارد شوید.",
    "login.error": "نام کاربری یا رمز عبور اشتباه است.",
    "login.username": "نام کاربری",
    "login.password": "رمز عبور",
    "login.submit": "ورود",
    "login.back": "بازگشت به خانه",
    "dashboard.logout": "خروج",
    "dashboard.eyebrow": "محیط هوشمند فارکس",
    "dashboard.title": "داشبورد تحلیل فارکس",
    "dashboard.user": "کاربر",
    "session.label": "سشن بازار",
    "mt5.eyebrow": "اتصال محلی حساب دمو",
    "mt5.title": "متاتریدر ۵",
    "mt5.disconnected": "قطع",
    "mt5.checking": "در حال بررسی اتصال…",
    "mt5.connected": "دمو متصل",
    "mt5.account": "حساب",
    "mt5.server": "سرور",
    "mt5.balance": "موجودی",
    "mt5.equity": "اکوئیتی",
    "mt5.margin": "مارجین",
    "mt5.mode": "حالت اجرا",
    "mt5.connect": "بررسی اتصال",
    "mt5.fetch": "دریافت کندل از MT5",
    "mt5.minStrength": "حداقل قدرت سیگنال",
    "mt5.maxSpread": "حداکثر اسپرد (واحد پایه)",
    "mt5.riskPercent": "ریسک هر سیگنال (%)",
    "mt5.maxVolume": "سقف حجم (لات)",
    "mt5.atrStop": "ضریب ATR حد ضرر",
    "mt5.rewardRisk": "نسبت سود به ریسک",
    "mt5.preview": "ساخت پیش‌نمایش سیگنال امن",
    "mt5.safety": "حالت امن فعال است: هیچ سفارشی ارسال نمی‌شود و کندل ناقص جاری کنار گذاشته می‌شود.",
    "mt5.loginRequired": "برای اتصال ترمینال محلی متاتریدر ۵ ابتدا وارد حساب شوید.",
    "mt5.login": "ورود",
    "live.title": "داده زنده قیمت",
    "live.symbol": "نماد، مثال: EUR/USD",
    "live.interval": "تایم‌فریم",
    "live.outputsize": "تعداد کندل",
    "live.fetch": "دریافت داده زنده",
    "manual.title": "داده دستی",
    "manual.prices": "قیمت‌های بسته شدن، جدا شده با کاما",
    "ind.useRsi": "استفاده از RSI",
    "ind.rsiPeriod": "حساسیت RSI",
    "ind.useMacd": "استفاده از MACD",
    "ind.macdShortPeriod": "بررسی روند سریع",
    "ind.macdLong": "فعال‌سازی روند کند MACD",
    "ind.macdLongPeriod": "بررسی روند کند",
    "ind.macdSignal": "فعال‌سازی سیگنال MACD",
    "ind.macdSignalPeriod": "نرم‌سازی سیگنال",
    "ind.tdigm": "فعال‌سازی TDIGM",
    "ind.tdigmValue": "اعتماد اضافه",
    "tip.rsiPeriod": "تعداد کندل‌هایی که RSI بررسی می‌کند. عدد کمتر سریع‌تر واکنش می‌دهد؛ عدد بیشتر نرم‌تر است.",
    "tip.macdShortPeriod": "میانگین سریع در MACD. عدد کمتر به تغییرات قیمت سریع‌تر واکنش می‌دهد.",
    "tip.macdLongPeriod": "میانگین کندتر در MACD. عدد بیشتر روی روند بزرگ‌تر تمرکز می‌کند.",
    "tip.macdSignalPeriod": "خط MACD را نرم‌تر می‌کند تا کراس‌ها خواناتر شوند.",
    "tip.tdigmValue": "وقتی شرط TDIGM شما فعال است کمی به اعتماد تحلیل اضافه می‌کند.",
    "ind.calculate": "محاسبه اندیکاتورها",
    "strategy.title": "پریست استراتژی",
    "strategy.scalp": "اسکالپ",
    "strategy.scalpNote": "سیگنال سریع برای نگهداری کوتاه.",
    "strategy.day": "معامله روزانه",
    "strategy.dayNote": "تنظیمات متعادل برای داخل روز.",
    "strategy.swing": "سوئینگ",
    "strategy.swingNote": "سیگنال نرم‌تر برای حرکت‌های بلندتر.",
    "strategy.goldDemo": "طلای H4 · پژوهش دمو",
    "strategy.goldDemoNote": "ستاپ H1/H4/D1 با تأیید AI و اجرای دستی فقط روی حساب دمو.",
    "setup.label": "ستاپ معامله",
    "setup.emptyTitle": "در انتظار محاسبه",
    "setup.emptyBadge": "بدون سیگنال",
    "setup.emptyReason": "اندیکاتورها را محاسبه کنید تا ستاپ بازار نمایش داده شود.",
    "setup.explain": "توضیح ستاپ",
    "setup.strength": "قدرت سیگنال",
    "tradePlan.title": "برنامه معامله",
    "tradePlan.entry": "محدوده ورود",
    "tradePlan.stop": "حد ضرر",
    "tradePlan.target": "حد سود",
    "tradePlan.rr": "سود/ریسک",
    "tradePlan.empty": "اندیکاتورها را محاسبه کنید تا برنامه تقریبی ساخته شود.",
    "risk.title": "محاسبه‌گر ریسک",
    "risk.balance": "موجودی حساب",
    "risk.percent": "ریسک هر معامله (%)",
    "risk.stopPips": "فاصله حد ضرر (پیپ)",
    "risk.pipValue": "ارزش هر پیپ برای ۱ لات",
    "risk.result": "حجم پیشنهادی پوزیشن",
    "decision.title": "پنل تصمیم",
    "decision.price": "آخرین قیمت",
    "decision.rsi": "آخرین RSI",
    "decision.rsiState": "وضعیت RSI",
    "decision.macdBias": "جهت MACD",
    "decision.cross": "کراس MACD",
    "decision.action": "پیشنهاد سیستم",
    "decision.confidence": "اعتماد",
    "decision.risk": "ریسک",
    "ai.title": "تحلیل هوشمند OpenAI",
    "ai.profile": "پروفایل معامله",
    "ai.scalp": "اسکالپ، بسیار کوتاه‌مدت",
    "ai.day": "روزانه، داخل روز",
    "ai.swing": "سوئینگ، چند ساعت تا چند روز",
    "ai.nds": "NDS، تایید سریع چندشرطی",
    "ai.holding": "حداکثر زمان نگهداری، دقیقه",
    "ai.analyze": "اجرای تحلیل هوشمند",
    "backtest.title": "بک‌تست استراتژی",
    "backtest.note": "در هر ورود فقط از اطلاعات همان لحظه استفاده می‌شود و هزینه رفت‌وبرگشت تخمینی هم لحاظ شده است.",
    "backtest.run": "اجرای بک‌تست",
    "backtest.holding": "تعداد کندل نگهداری",
    "backtest.fee": "هزینه و اسپرد هر سمت (bps)",
    "backtest.trades": "تعداد معاملات",
    "backtest.winRate": "نرخ برد",
    "backtest.totalReturn": "بازده کل",
    "backtest.profitFactor": "ضریب سود",
    "backtest.expectancy": "امید ریاضی هر معامله",
    "backtest.drawdown": "بیشترین افت سرمایه",
    "backtest.sharpe": "نسبت شارپ معاملاتی",
    "backtest.needData": "برای بک‌تست حداقل ۵۰ قیمت معتبر لازم است.",
    "backtest.failed": "اجرای بک‌تست ناموفق بود.",
    "backtest.connection": "ارتباط با سرویس بک‌تست برقرار نشد.",
    "backtest.warning": "عملکرد گذشته تضمینی برای نتیجه آینده نیست.",
    "backtest.noTrades": "هیچ موقعیت تاریخی با قانون انتخاب‌شده منطبق نبود.",
    "history.title": "تاریخچه تحلیل و تصمیم‌های خودکار",
    "history.refresh": "به‌روزرسانی",
    "journal.title": "ژورنال معاملات",
    "journal.save": "ذخیره معامله",
    "journal.buy": "خرید",
    "journal.sell": "فروش",
    "journal.entry": "قیمت ورود",
    "journal.stop": "حد ضرر",
    "journal.target": "حد سود",
    "journal.exit": "قیمت خروج (اختیاری)",
    "journal.open": "باز",
    "journal.won": "سودده",
    "journal.lost": "زیان‌ده",
    "journal.cancelled": "لغوشده",
    "journal.notes": "یادداشت",
    "mentor.role": "استاد معامله‌گری و مشاور تحلیل",
    "mentor.name": "استاد کاوش",
    "mentor.available": "آماده راهنمایی",
    "mentor.welcome": "کمکت می‌کنم تحلیل را بفهمی، ریسک را بررسی کنی و قبل از ورود، پلن معامله‌ات را بسنجی. ابتدا داده بازار را دریافت کن.",
    "mentor.education": "به من آموزش بده",
    "mentor.advice": "به من مشاوره بده",
    "mentor.review": "معامله‌ام را بررسی کن",
    "mentor.educationSeed": "استاد، مفهوم اندیکاتورهای فعلی و روش درست خواندن آن‌ها را به من آموزش بده.",
    "mentor.adviceSeed": "استاد، درباره وضعیت فعلی با تمرکز بر ریسک و دلایل صبر کردن به من مشاوره بده.",
    "mentor.reviewSeed": "استاد، پلن فعلی من شامل ورود، حد ضرر، حد سود و ریسک معامله را بررسی کن.",
  },
};

const uiText = {
  en: {
    fetchError: "Failed to fetch live data.",
    fetchConnectionError: "Could not connect to the server for live prices.",
    minPrices: "At least 30 valid prices are required.",
    calculateError: "Failed to calculate indicators.",
    serverError: "Could not connect to the server.",
    analyzeFirst: "Calculate indicators first.",
    analyzeFirstStatus: "To run smart analysis, calculate indicators first.",
    aiSending: "Sending request to OpenAI and waiting for analysis...",
    aiError: "Smart analysis failed. Please try again.",
    aiConnectionError: "Could not connect to OpenAI.",
    aiDone: "Analysis received and displayed below.",
    aiUnavailable: "Analysis service connection failed.",
    minute: "minutes",
    disabled: "Disabled",
    overbought: "Overbought",
    oversold: "Oversold",
    neutral: "Neutral",
    bullish: "Bullish",
    bearish: "Bearish",
    noCross: "None",
    bullishCross: "Bullish cross",
    bearishCross: "Bearish cross",
    wait: "Wait",
    buyBias: "Buy bias",
    sellBias: "Sell bias",
    cautiousBuy: "Cautious buy",
    cautiousSell: "Cautious sell",
    activeWatch: "Active watch (TDIGM)",
    medium: "Medium",
    lowMedium: "Low to medium",
    high: "High",
    note: "This output is an analysis tool only and is not a guaranteed buy/sell signal.",
    noTradePlan: "The current setup is not clear enough for a trade plan. Wait for a cleaner direction before planning levels.",
    planNote: "Estimated levels are based on recent volatility. Check spread, session liquidity, and broker rules before trading.",
    setupEmpty: "There are not enough active signals yet.",
    explainFirst: "Calculate indicators first; then this section explains why the setup was selected.",
    atRisk: "at risk",
    lots: "lots",
    aiLabels: {
      market_state: "Market state",
      profile_used: "Profile used",
      action_bias: "Trading bias",
      confidence: "Confidence",
      execution_type: "Execution type",
      holding_time_minutes: "Suggested holding time",
      liquidity_note: "Liquidity note",
      entry_idea: "Entry idea",
      stop_loss_idea: "Stop-loss idea",
      take_profit_idea: "Take-profit idea",
      nds_checklist: "NDS checklist",
      why: "Reasons",
      risk_warnings: "Risk warnings",
    },
  },
  fa: {
    fetchError: "دریافت داده زنده ناموفق بود.",
    fetchConnectionError: "اتصال به سرور برای قیمت‌های زنده برقرار نشد.",
    minPrices: "حداقل ۳۰ قیمت معتبر لازم است.",
    calculateError: "محاسبه اندیکاتورها ناموفق بود.",
    serverError: "اتصال به سرور برقرار نشد.",
    analyzeFirst: "اول اندیکاتورها را محاسبه کنید.",
    analyzeFirstStatus: "برای تحلیل هوشمند، ابتدا اندیکاتورها را محاسبه کنید.",
    aiSending: "در حال ارسال درخواست به OpenAI و دریافت تحلیل...",
    aiError: "تحلیل هوشمند ناموفق بود. دوباره تلاش کنید.",
    aiConnectionError: "اتصال به OpenAI برقرار نشد.",
    aiDone: "تحلیل دریافت و نمایش داده شد.",
    aiUnavailable: "اتصال سرویس تحلیل ناموفق بود.",
    minute: "دقیقه",
    disabled: "غیرفعال",
    overbought: "اشباع خرید",
    oversold: "اشباع فروش",
    neutral: "خنثی",
    bullish: "صعودی",
    bearish: "نزولی",
    noCross: "بدون کراس",
    bullishCross: "کراس صعودی",
    bearishCross: "کراس نزولی",
    wait: "صبر",
    buyBias: "تمایل خرید",
    sellBias: "تمایل فروش",
    cautiousBuy: "خرید محتاطانه",
    cautiousSell: "فروش محتاطانه",
    activeWatch: "رصد فعال با TDIGM",
    medium: "متوسط",
    lowMedium: "کم تا متوسط",
    high: "بالا",
    noTradePlan: "وضعیت فعلی برای معامله واضح نیست. برای برنامه‌ریزی سطوح، منتظر جهت روشن‌تر بمانید.",
    planNote: "سطوح تقریبی بر اساس نوسان اخیر هستند. اسپرد، نقدشوندگی سشن و قوانین بروکر را بررسی کنید.",
    setupEmpty: "هنوز سیگنال‌های فعال کافی وجود ندارد.",
    explainFirst: "اول اندیکاتورها را محاسبه کنید؛ بعد این بخش دلیل انتخاب ستاپ را توضیح می‌دهد.",
    atRisk: "در معرض ریسک",
    lots: "لات",
    note: "این خروجی فقط ابزار تحلیلی است و سیگنال قطعی خرید یا فروش نیست.",
    aiLabels: {
      market_state: "وضعیت بازار",
      profile_used: "پروفایل استفاده‌شده",
      action_bias: "جهت معامله",
      confidence: "اعتماد",
      execution_type: "نوع اجرا",
      holding_time_minutes: "زمان نگهداری پیشنهادی",
      liquidity_note: "نکته نقدشوندگی",
      entry_idea: "ایده ورود",
      stop_loss_idea: "ایده حد ضرر",
      take_profit_idea: "ایده حد سود",
      nds_checklist: "چک‌لیست NDS",
      why: "دلایل",
      risk_warnings: "هشدارهای ریسک",
    },
  },
};

let priceChart;
let rsiChart;
let macdChart;
let latestComputed = null;
let latestAiPayload = null;
let latestBacktestResult = null;
let latestSetupExplanation = "";
let currentMentorMode = "education";
let latestMarketData = { opens: null, highs: null, lows: null, labels: null, market: null, quality: null };
let pendingExecutionToken = null;
let pendingExecutionPlan = null;
let observedCandleStartMs = null;
let autoCandleCyclePending = false;
let mt5ServerClockOffsetMs = 0;
let observedDemoHourSlotMs = null;
let currentDemoHourSlot = null;
let currentDemoHourVolume = 0.01;
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
let currentLanguage = localStorage.getItem("tradeaiLanguage") || "fa";
if (!translations[currentLanguage]) {
  currentLanguage = "en";
}

const strategyPresets = {
  goldDemo: {
    symbol: "XAU/USD",
    interval: "4h",
    outputsize: 500,
    rsi: 21,
    macdShort: 8,
    macdLong: 21,
    macdSignal: 5,
    holding: 1440,
    holdingBars: 12,
    feeBps: 2,
    aiProfile: "swing",
    atrStopMultiple: 2.0,
    rewardRisk: 2.0,
    riskPercent: 0.1,
    minimumStrength: 70,
    maximumSpreadBps: 3,
    maximumVolume: 0.1,
    maximumDailyLoss: 1,
    maximumDailyTrades: 20,
    minimumAiConfidence: 70,
  },
  goldM15Demo: {
    symbol: "XAU/USD",
    interval: "15min",
    outputsize: 500,
    rsi: 14,
    macdShort: 12,
    macdLong: 26,
    macdSignal: 9,
    holding: 90,
    holdingBars: 6,
    feeBps: 2,
    aiProfile: "day",
    atrStopMultiple: 1.5,
    rewardRisk: 2.5,
    riskPercent: 0.1,
    minimumStrength: 80,
    maximumSpreadBps: 3,
    maximumVolume: 0.01,
    maximumDailyLoss: 0.25,
    maximumDailyTrades: 20,
    minimumAiConfidence: 80,
  },
  eurDemo: {
    symbol: "EUR/USD", interval: "4h", outputsize: 500,
    rsi: 21, macdShort: 12, macdLong: 26, macdSignal: 9,
    holding: 1440, holdingBars: 6, feeBps: 2, aiProfile: "swing",
    atrStopMultiple: 1.5, rewardRisk: 1.0, riskPercent: 0.1,
    minimumStrength: 75, maximumSpreadBps: 3, maximumVolume: 0.01,
    maximumDailyLoss: 0.5, maximumDailyTrades: 20, minimumAiConfidence: 75,
  },
  gbpDemo: {
    symbol: "GBP/USD", interval: "4h", outputsize: 500,
    rsi: 21, macdShort: 12, macdLong: 26, macdSignal: 9,
    holding: 720, holdingBars: 3, feeBps: 2, aiProfile: "swing",
    atrStopMultiple: 1.5, rewardRisk: 1.5, riskPercent: 0.1,
    minimumStrength: 75, maximumSpreadBps: 3, maximumVolume: 0.01,
    maximumDailyLoss: 0.5, maximumDailyTrades: 20, minimumAiConfidence: 75,
  },
  jpyDemo: {
    symbol: "USD/JPY", interval: "4h", outputsize: 500,
    rsi: 21, macdShort: 12, macdLong: 26, macdSignal: 9,
    holding: 2880, holdingBars: 12, feeBps: 2, aiProfile: "swing",
    atrStopMultiple: 1.5, rewardRisk: 2.5, riskPercent: 0.1,
    minimumStrength: 75, maximumSpreadBps: 3, maximumVolume: 0.01,
    maximumDailyLoss: 0.5, maximumDailyTrades: 20, minimumAiConfidence: 75,
  },
};

// Strategy selection belongs before execution controls: choose first, then analyze.
const strategyPresetPanel = document.getElementById("strategyPresetPanel");
const mt5ExecutionCard = document.getElementById("mt5Card");
if (strategyPresetPanel && mt5ExecutionCard) {
  mt5ExecutionCard.parentNode?.insertBefore(strategyPresetPanel, mt5ExecutionCard);
}

function t(key) {
  return (
    uiText[currentLanguage]?.[key]
    || translations[currentLanguage]?.[key]
    || uiText.en[key]
    || translations.en[key]
    || key
  );
}

function translateValue(value) {
  if (!value) {
    return "-";
  }
  const valueMap = {
    Disabled: "disabled",
    Overbought: "overbought",
    Oversold: "oversold",
    Neutral: "neutral",
    Bullish: "bullish",
    Bearish: "bearish",
    None: "noCross",
    "Bullish cross": "bullishCross",
    "Bearish cross": "bearishCross",
    Wait: "wait",
    "Buy bias": "buyBias",
    "Sell bias": "sellBias",
    "Cautious buy": "cautiousBuy",
    "Cautious sell": "cautiousSell",
    "Active watch (TDIGM)": "activeWatch",
    Medium: "medium",
    "Low to medium": "lowMedium",
    High: "high",
    "This output is an analysis tool only and is not a guaranteed buy/sell signal.": "note",
  };
  const key = valueMap[value];
  return key ? t(key) : value;
}

function applyLanguage() {
  const dictionary = translations[currentLanguage] || translations.en;
  document.documentElement.lang = currentLanguage === "fa" ? "fa" : "en";
  document.documentElement.dir = currentLanguage === "fa" ? "rtl" : "ltr";

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (dictionary[key]) {
      element.textContent = dictionary[key];
    }
  });

  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    const key = element.dataset.i18nTitle;
    if (dictionary[key]) {
      element.title = dictionary[key];
    }
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const key = element.dataset.i18nPlaceholder;
    if (dictionary[key]) {
      element.placeholder = dictionary[key];
    }
  });

  const languageToggle = document.getElementById("languageToggle");
  if (languageToggle) {
    languageToggle.textContent = currentLanguage === "fa" ? "EN" : "FA";
    languageToggle.setAttribute("aria-label", currentLanguage === "fa" ? "Switch to English" : "تغییر زبان به فارسی");
  }

  updateMarketSession();

  if (latestComputed && latestComputed.summary) {
    updateDecision(latestComputed.summary);
  }
  if (latestAiPayload) {
    renderAiResult(latestAiPayload);
  }
  if (latestBacktestResult) {
    renderBacktest(latestBacktestResult);
  }
}

applyLanguage();

const form = document.getElementById("indicatorForm");
const errorBox = document.getElementById("errorBox");
const fetchLiveBtn = document.getElementById("fetchLiveBtn");
const aiAnalyzeBtn = document.getElementById("aiAnalyzeBtn");
const aiStatus = document.getElementById("aiStatus");
const aiProgress = document.getElementById("aiProgress");
const explainBtn = document.getElementById("explainBtn");
const explainText = document.getElementById("explainText");
const mt5Card = document.getElementById("mt5Card");
const mt5ConnectBtn = document.getElementById("mt5ConnectBtn");
const mt5FetchBtn = document.getElementById("mt5FetchBtn");
const mt5SignalBtn = document.getElementById("mt5SignalBtn");
const quickDemoAnalyzeBtn = document.getElementById("quickDemoAnalyzeBtn");
const expensiveAiReviewBtn = document.getElementById("expensiveAiReviewBtn");

function parsePrices(text) {
  return text
    .split(",")
    .map((v) => v.trim())
    .filter((v) => v.length > 0)
    .map((v) => Number(v));
}

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if ((options.method || "GET").toUpperCase() !== "GET" && csrfToken) {
    headers.set("X-CSRF-Token", csrfToken);
  }
  const response = await fetch(url, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { error: await response.text() };
  return { response, data };
}

function setMt5ConnectionState(connected, label) {
  const status = document.getElementById("mt5Status");
  if (!status) return;
  const checking = connected === "checking";
  status.classList.toggle("checking", checking);
  status.classList.toggle("offline", !connected && !checking);
  const text = status.querySelector("span");
  if (text) text.textContent = label || (connected ? t("mt5.connected") : t("mt5.disconnected"));
}

function formatAccountMoney(value, currency) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "-";
  return `${amount.toLocaleString(currentLanguage === "fa" ? "fa-IR" : "en-US", {
    maximumFractionDigits: 2,
  })} ${currency || ""}`.trim();
}

function renderMt5Status(payload) {
  const account = payload?.account || {};
  const portfolio = payload?.portfolio || {};
  const connected = Boolean(payload?.connected);
  const tradingReady = Boolean(payload?.terminal_trade_allowed && account.trade_allowed && account.expert_allowed);
  const statusLabel = connected
    ? (tradingReady
      ? (currentLanguage === "fa" ? "متصل و آماده معامله دمو" : "Connected and demo-ready")
      : (currentLanguage === "fa" ? "متصل؛ اجرای معامله غیرفعال" : "Connected; trading disabled"))
    : t("mt5.disconnected");
  setMt5ConnectionState(connected, statusLabel);
  const values = {
    mt5Account: `${account.login_masked || "-"} · ${(account.trade_mode || "-").toUpperCase()}`,
    mt5Server: account.server || "-",
    mt5Balance: formatAccountMoney(account.balance, account.currency),
    mt5Equity: formatAccountMoney(account.equity, account.currency),
    mt5Margin: formatAccountMoney(account.margin, account.currency),
    mt5OpenPositions: Number.isFinite(Number(portfolio.open_position_count)) ? String(portfolio.open_position_count) : "-",
    mt5DailyTrades: Number.isFinite(Number(portfolio.daily_trade_count)) ? String(portfolio.daily_trade_count) : "-",
    mt5DailyNet: Number.isFinite(Number(portfolio.daily_realized_net)) ? formatAccountMoney(portfolio.daily_realized_net, account.currency) : "-",
    mt5Mode: payload.execution_mode || "signal_only",
  };
  Object.entries(values).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  });
  const balanceInput = document.getElementById("accountBalance");
  if (balanceInput && Number(account.equity) > 0) {
    balanceInput.value = Number(account.equity).toFixed(2);
    updateRiskCalculator();
  }
}

async function checkMt5Connection() {
  if (!mt5ConnectBtn) return;
  mt5ConnectBtn.disabled = true;
  hideError();
  setMt5ConnectionState("checking", t("mt5.checking"));
  try {
    const { response, data } = await apiFetch("mt5/status");
    if (!response.ok || !data.ok) throw new Error(data.error || "MT5 connection failed.");
    const serverEpoch = Number(data.server_clock?.epoch_seconds || 0);
    if (serverEpoch > 0) mt5ServerClockOffsetMs = (serverEpoch * 1000) - Date.now();
    renderMt5Status(data);
  } catch (error) {
    setMt5ConnectionState(false, t("mt5.disconnected"));
    showError(error?.message || "MT5 connection failed.");
  } finally {
    mt5ConnectBtn.disabled = false;
  }
}

async function loadMt5Candles() {
  if (!mt5FetchBtn) return;
  mt5FetchBtn.disabled = true;
  hideError();
  const payload = {
    symbol: document.getElementById("symbol")?.value || "EUR/USD",
    interval: document.getElementById("interval")?.value || "15min",
    outputsize: Number(document.getElementById("outputsize")?.value || 300),
  };
  try {
    const { response, data } = await apiFetch("mt5/market-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok || !data.ok) throw new Error(data.error || "MT5 market data failed.");
    renderMt5Status({
      connected: true,
      execution_mode: data.execution_mode,
      terminal_trade_allowed: data.terminal_trade_allowed,
      account: data.account,
      portfolio: data.portfolio,
    });
    document.getElementById("symbol").value = data.symbol;
    document.getElementById("prices").value = data.prices.join(",");
    latestMarketData = {
      opens: data.opens || null,
      highs: data.highs || null,
      lows: data.lows || null,
      labels: data.labels || null,
      market: data.market || null,
      quality: data.quality || null,
      provider: data.provider || "MetaTrader 5",
    };
    const market = data.market || {};
    const marketText = document.getElementById("mt5Market");
    if (marketText) {
      marketText.textContent = `${market.symbol || data.symbol} · Bid ${market.bid ?? "-"} · Ask ${market.ask ?? "-"} · Spread ${market.spread_pips ?? "-"} pip`;
    }
    const pipValue = document.getElementById("pipValue");
    if (pipValue && market.pip_size && market.trade_tick_size && market.trade_tick_value) {
      pipValue.value = ((market.pip_size / market.trade_tick_size) * market.trade_tick_value).toFixed(4);
      updateRiskCalculator();
    }
    if (!data.quality?.safe_for_signal) {
      showError(currentLanguage === "fa"
        ? "داده دریافت شد، اما به‌دلیل فاصله یا ردیف نامعتبر برای سیگنال خودکار ایمن نیست."
        : "Data loaded, but gaps or invalid rows make it unsafe for an automated signal.");
    }
  } catch (error) {
    showError(error?.message || "MT5 market data failed.");
  } finally {
    mt5FetchBtn.disabled = false;
  }
}

function renderMt5Signal(payload) {
  const box = document.getElementById("mt5SignalResult");
  if (!box) return;
  const signal = payload.signal || {};
  const plan = payload.risk_plan;
  const displaySignal = signal.display_signal || signal.signal || "HOLD";
  const tone = String(displaySignal).toLowerCase().replace(/\s+/g, "-");
  const reasons = Array.isArray(signal.reasons) ? signal.reasons : [];
  const ai = payload.ai_assessment || {};
  const aiReasons = Array.isArray(ai.reasons) ? ai.reasons : [];
  const aiInvalidators = Array.isArray(ai.invalidators) ? ai.invalidators : [];
  const mtf = payload.timeframe_confirmation || {};
  const macro = payload.macro_gate || {};
  const market = payload.market || {};
  const intelligence = payload.market_intelligence || {};
  const regime = intelligence.regime || {};
  const drift = intelligence.drift || {};
  const route = intelligence.strategy_route || {};
  const demoLab = payload.execution_tier === "demo_lab";
  const experimental = payload.execution_tier === "experimental_forward_demo";
  const tierHtml = demoLab
    ? `<p class="mt5-safety">${currentLanguage === "fa"
      ? "آزمایشگاه DEMO: خروجی فقط BUY یا SELL است و خبر، AI و چندتایم‌فریم آن را متوقف نمی‌کنند. این آزمایش است و وعده سود نیست."
      : "DEMO LAB: output is BUY or SELL only; news, AI, and multi-timeframe checks do not veto it. This is an experiment, not a profit promise."}</p>`
    : experimental
    ? `<p class="mt5-safety">${currentLanguage === "fa"
      ? "هشدار: این پروفایل بک‌تست قبولی ندارد و فقط برای جمع‌آوری داده Forward روی حساب دمو فعال است."
      : "Warning: this profile did not pass backtesting and is enabled only for forward data collection on DEMO."}</p>`
    : "";
  const planHtml = plan ? `
    <div class="ai-trade-grid">
      <section class="ai-trade-card"><span>${currentLanguage === "fa" ? "ورود" : "Entry"}</span><strong>${escapeHtml(plan.entry)}</strong></section>
      <section class="ai-trade-card"><span>${currentLanguage === "fa" ? "حد ضرر" : "Stop loss"}</span><strong>${escapeHtml(plan.stop_loss)}</strong></section>
      <section class="ai-trade-card"><span>${currentLanguage === "fa" ? "حد سود" : "Take profit"}</span><strong>${escapeHtml(plan.take_profit)}</strong></section>
      <section class="ai-trade-card"><span>${currentLanguage === "fa" ? "حجم محاسبه‌شده" : "Calculated volume"}</span><strong>${escapeHtml(plan.volume)} lot</strong></section>
      <section class="ai-trade-card"><span>${currentLanguage === "fa" ? "ریسک تخمینی" : "Estimated risk"}</span><strong>${escapeHtml(plan.estimated_risk_amount)} ${escapeHtml(plan.currency)}</strong></section>
      <section class="ai-trade-card"><span>${currentLanguage === "fa" ? "ریسک مؤثر" : "Effective risk"}</span><strong>${escapeHtml(plan.risk_percent_effective)}%</strong></section>
    </div>` : "";
  const aiReviewHtml = payload.deep_ai_review ? `
    <section class="ai-review-summary">
      <strong>نظر دوم AI · ${escapeHtml(ai.decision || "uncertain")} · ${escapeHtml(ai.confidence ?? 0)}/100</strong>
      <small>مدل: ${escapeHtml(ai.model || "-")} · وضعیت بازار: ${escapeHtml(ai.regime || "-")} · ریسک خبر: ${escapeHtml(ai.news_risk || "unknown")}</small>
      ${aiReasons.length ? `<ul>${aiReasons.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}
      ${aiInvalidators.length ? `<p class="muted">موارد مخالف: ${aiInvalidators.map(escapeHtml).join(" · ")}</p>` : ""}
    </section>` : "";
  box.className = `mt5-signal-result signal-${tone}`;
  box.innerHTML = `
    <h3>${escapeHtml(displaySignal)} · ${escapeHtml(signal.symbol || "-")}</h3>
    <p>${currentLanguage === "fa" ? "قدرت اندیکاتور / ترکیبی" : "Indicator / combined strength"}: ${escapeHtml(signal.indicator_strength ?? "-")}/${escapeHtml(signal.combined_strength ?? "-")} · ${escapeHtml(signal.candle_time || "-")}</p>
    <div class="ai-trade-grid">
      <section class="ai-trade-card"><span>AI</span><strong>${escapeHtml(ai.decision || "-")} · ${escapeHtml(ai.confidence ?? 0)}/100</strong></section>
      <section class="ai-trade-card"><span>Regime</span><strong>${escapeHtml(regime.regime || "-")} · ${escapeHtml(regime.confidence ?? 0)}/100</strong></section>
      <section class="ai-trade-card"><span>Drift</span><strong>${escapeHtml(drift.level || "-")}</strong></section>
      <section class="ai-trade-card"><span>Router</span><strong>${escapeHtml(route.recommended_interval || "HOLD")} · ${escapeHtml(route.decision || "-")}</strong></section>
      <section class="ai-trade-card"><span>H1/H4/D1</span><strong>${escapeHtml(mtf.aligned ? "تأیید" : "رد")} · ${escapeHtml(mtf.score ?? 0)}/100</strong></section>
      <section class="ai-trade-card"><span>خبر</span><strong>${escapeHtml(demoLab ? "اطلاعاتی؛ بدون وتو" : (macro.clear ? "شفاف" : "مسدود"))}</strong></section>
      <section class="ai-trade-card"><span>تازگی قیمت</span><strong>${escapeHtml(market.tick_age_seconds ?? "-")} ثانیه</strong></section>
    </div>
    ${planHtml}
    ${aiReviewHtml}
    ${tierHtml}
    <ul>${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
    <p class="mt5-safety">${currentLanguage === "fa" ? "این خروجی احتمال سود نیست و هیچ سفارشی ارسال نشده است." : "This is not a profit probability and no order was sent."}</p>
  `;
  box.classList.remove("hidden");
  pendingExecutionToken = payload.execution_ready ? payload.execution_token : null;
  pendingExecutionPlan = pendingExecutionToken && plan ? { ...plan, direction: displaySignal } : null;
  const executionPanel = document.getElementById("demoExecutionPanel");
  const executionStatus = document.getElementById("demoExecutionStatus");
  const confirmation = document.getElementById("demoConfirmation");
  if (executionPanel) executionPanel.classList.toggle("hidden", !pendingExecutionToken);
  if (executionStatus) executionStatus.textContent = pendingExecutionToken ? "پلن توسط کارگزاری بررسی شد؛ ۵ دقیقه برای تأیید فرصت دارید." : "";
  if (confirmation) confirmation.value = "";
  const quickFields = {
    quickDirection: displaySignal,
    quickEntry: plan?.entry ?? "",
    quickVolume: plan?.volume ?? "",
    quickStopLoss: plan?.stop_loss ?? "",
    quickTakeProfit: plan?.take_profit ?? "",
  };
  Object.entries(quickFields).forEach(([id, value]) => {
    const input = document.getElementById(id);
    if (input) input.value = value;
  });
}

async function buildMt5SignalPreview(options = {}) {
  if (!mt5SignalBtn) return;
  mt5SignalBtn.disabled = true;
  hideError();
  try {
    const requestPayload = {
      symbol: options?.quick === true ? "XAUUSD" : (document.getElementById("symbol")?.value || "EUR/USD"),
      interval: options?.quick === true ? "4h" : (document.getElementById("interval")?.value || "15min"),
      outputsize: Number(document.getElementById("outputsize")?.value || 300),
      minimum_strength: Number(document.getElementById("mt5MinStrength")?.value || 65),
      maximum_spread_bps: Number(document.getElementById("mt5MaxSpread")?.value || 3),
      risk_percent: Number(document.getElementById("mt5RiskPercent")?.value || 0.1),
      maximum_volume: Number(document.getElementById("mt5MaxVolume")?.value || 0.1),
      atr_stop_multiple: Number(document.getElementById("mt5AtrStop")?.value || 1.5),
      reward_risk: Number(document.getElementById("mt5RewardRisk")?.value || 2.5),
      maximum_daily_loss_percent: Number(document.getElementById("mt5DailyLoss")?.value || 1),
      maximum_open_positions: 4,
      maximum_consecutive_losses: Number(document.getElementById("mt5LossStreak")?.value || 2),
      loss_cooldown_hours: Number(document.getElementById("mt5LossCooldown")?.value || 12),
      maximum_daily_trades: Number(document.getElementById("mt5DailyTradesLimit")?.value || 20),
      ai_minimum_confidence: Number(document.getElementById("mt5AiConfidence")?.value || 70),
      rsi_period: Number(document.getElementById("rsiPeriod")?.value || 14),
      macd_short_period: Number(document.getElementById("macdShort")?.value || 12),
      macd_long_period: Number(document.getElementById("macdLong")?.value || 26),
      macd_signal_period: Number(document.getElementById("macdSignal")?.value || 9),
      demo_lab_mode: options?.quick === true || Boolean(document.getElementById("demoLabMode")?.checked),
      demo_lab_slot: options?.quick === true ? `quick-${Date.now()}` : (options?.demoLabSlot || null),
      demo_lab_volume: options?.quick === true
        ? Number(options?.defaultVolume ?? currentDemoHourVolume)
        : (options?.demoLabVolume || 0.01),
      disable_ai: options?.noAi === true,
      primary_ai_review: options?.primaryReview === true,
      deep_ai_review: options?.expensiveReview === true,
      analysis_only: options?.analysisOnly === true,
    };
    const { response, data } = await apiFetch("mt5/signal-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload),
    });
    if (!response.ok || !data.ok) throw new Error(data.error || "Signal preview failed.");
    renderMt5Status({
      connected: true,
      execution_mode: data.execution_mode,
      terminal_trade_allowed: data.terminal_trade_allowed,
      account: data.account,
      portfolio: data.portfolio,
    });
    renderMt5Signal(data);
    if (data.summary) updateMentorMessage(data.summary);
    const market = data.market || {};
    const marketText = document.getElementById("mt5Market");
    if (marketText) {
      marketText.textContent = `${market.symbol || "-"} · Bid ${market.bid ?? "-"} · Ask ${market.ask ?? "-"} · Spread ${market.spread_pips ?? "-"} pip`;
    }
    return data;
  } catch (error) {
    showError(error?.message || "Signal preview failed.");
    return null;
  } finally {
    mt5SignalBtn.disabled = false;
  }
}

async function executeDemoOrder(options = {}) {
  const button = document.getElementById("demoExecuteBtn");
  const confirmation = document.getElementById("demoConfirmation");
  const status = document.getElementById("demoExecutionStatus");
  if (!button || !pendingExecutionToken) return;
  const automatic = options?.automatic === true;
  if (!automatic && (confirmation?.value || "").trim().toUpperCase() !== "DEMO") {
    if (status) status.textContent = "برای تأیید، عبارت DEMO را دقیق وارد کنید.";
    return;
  }
  button.disabled = true;
  if (status) status.textContent = "در حال بررسی مجدد و ارسال سفارش دمو…";
  try {
    const { response, data } = await apiFetch("mt5/execute-demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        execution_token: pendingExecutionToken,
        confirmation: "DEMO",
        plan_overrides: automatic ? null : {
          volume: Number(document.getElementById("quickVolume")?.value),
          stop_loss: Number(document.getElementById("quickStopLoss")?.value),
          take_profit: Number(document.getElementById("quickTakeProfit")?.value),
        },
      }),
    });
    if (!response.ok || !data.ok) throw new Error(data.error || "Demo order failed.");
    pendingExecutionToken = null;
    pendingExecutionPlan = null;
    document.getElementById("demoExecutionPanel")?.classList.add("hidden");
    const result = data.result || {};
    if (status) status.textContent = `سفارش دمو ثبت شد: order ${result.order || "-"} · deal ${result.deal || "-"}`;
    const box = document.getElementById("mt5SignalResult");
    if (box) box.insertAdjacentHTML("beforeend", `<p class="success">سفارش DEMO ارسال شد · Order ${escapeHtml(result.order || "-")} · Deal ${escapeHtml(result.deal || "-")}</p>`);
    if (automatic) setAutoCandleStatus(`سفارش DEMO ارسال شد · Order ${result.order || "-"} · Deal ${result.deal || "-"}`);
    loadJournal();
    checkMt5Connection();
  } catch (error) {
    pendingExecutionToken = null;
    pendingExecutionPlan = null;
    const message = error?.message || "نتیجه سفارش نامشخص است؛ MT5 را بررسی کنید.";
    // Keep the confirmation panel visible: previously it was hidden before
    // writing the error, so the user only heard the alert sound.
    document.getElementById("demoExecutionPanel")?.classList.remove("hidden");
    showError(message);
    if (status) status.textContent = `${message} برای تلاش دوباره، تحلیل تازه بگیرید.`;
    const box = document.getElementById("mt5SignalResult");
    if (box) box.insertAdjacentHTML("beforeend", `<p class="error">${escapeHtml(message)} برای تلاش دوباره، تحلیل تازه بگیرید.</p>`);
    if (automatic) setAutoCandleStatus(error?.message || "ارسال خودکار سفارش DEMO ناموفق بود.");
  } finally {
    button.disabled = false;
  }
}

function buildLabels(length) {
  return Array.from({ length }, (_, i) => i + 1);
}

function showError(message) {
  if (!errorBox) {
    return;
  }
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  if (!errorBox) {
    return;
  }
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function syncIndicatorInputs() {
  const useRsi = document.getElementById("useRsi").checked;
  const useMacd = document.getElementById("useMacd").checked;
  const useMacdLong = document.getElementById("useMacdLong").checked;
  const useMacdSignal = document.getElementById("useMacdSignal").checked;
  const useTdigm = document.getElementById("useTdigm").checked;

  document.getElementById("rsiPeriod").disabled = !useRsi;
  document.getElementById("macdShort").disabled = !useMacd;
  document.getElementById("macdLong").disabled = !useMacd || !useMacdLong;
  document.getElementById("macdSignal").disabled = !useMacd || !useMacdSignal;
  document.getElementById("tdigmValue").disabled = !useTdigm;
}

function formatNum(value, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function getPipSize() {
  const symbol = (document.getElementById("symbol").value || "").toUpperCase();
  return symbol.includes("JPY") ? 0.01 : 0.0001;
}

function averageMove(prices) {
  if (!Array.isArray(prices) || prices.length < 2) {
    return 0;
  }
  const slice = prices.slice(-20);
  const moves = [];
  for (let i = 1; i < slice.length; i += 1) {
    moves.push(Math.abs(Number(slice[i]) - Number(slice[i - 1])));
  }
  return moves.reduce((sum, value) => sum + value, 0) / Math.max(1, moves.length);
}

function getSetupDirection(action) {
  const normalized = String(action || "").toLowerCase();
  if (normalized.includes("buy")) {
    return "buy";
  }
  if (normalized.includes("sell")) {
    return "sell";
  }
  return "wait";
}

function translateFactorText(text) {
  if (currentLanguage !== "fa") {
    return text;
  }
  const aboveMatch = String(text).match(/^MACD is above signal by (.+)\.$/);
  if (aboveMatch) {
    return `MACD به اندازه ${aboveMatch[1]} بالاتر از خط سیگنال است.`;
  }
  const belowMatch = String(text).match(/^MACD is below signal by (.+)\.$/);
  if (belowMatch) {
    return `MACD به اندازه ${belowMatch[1]} پایین‌تر از خط سیگنال است.`;
  }
  return String(text)
    .replace("MACD histogram is positive.", "هیستوگرام MACD مثبت است.")
    .replace("MACD histogram is negative.", "هیستوگرام MACD منفی است.")
    .replace("MACD histogram is improving.", "هیستوگرام MACD در حال بهتر شدن است.")
    .replace("MACD histogram is weakening.", "هیستوگرام MACD در حال ضعیف شدن است.")
    .replace("Fresh bullish MACD cross.", "کراس صعودی تازه در MACD دیده می‌شود.")
    .replace("Fresh bearish MACD cross.", "کراس نزولی تازه در MACD دیده می‌شود.")
    .replace("Recent price movement is upward.", "حرکت اخیر قیمت صعودی است.")
    .replace("Recent price movement is downward.", "حرکت اخیر قیمت نزولی است.")
    .replace("RSI supports bullish momentum without being overbought.", "RSI از مومنتوم صعودی حمایت می‌کند و هنوز اشباع خرید نیست.")
    .replace("RSI supports bearish momentum without being oversold.", "RSI از مومنتوم نزولی حمایت می‌کند و هنوز اشباع فروش نیست.")
    .replace("RSI is overbought, reducing buy quality.", "RSI در اشباع خرید است و کیفیت خرید را کمتر می‌کند.")
    .replace("RSI is oversold, reducing sell quality.", "RSI در اشباع فروش است و کیفیت فروش را کمتر می‌کند.")
    .replace("TDIGM adds extra confirmation weight.", "TDIGM وزن تایید اضافه می‌کند.");
}

function buildSetup(summary) {
  const confidence = Math.max(0, Math.min(100, Number(summary.confidence) || 0));
  const action = summary.action_bias || "Wait";
  const macd = summary.macd_bias || "Disabled";
  const rsi = summary.rsi_state || "Disabled";
  const cross = summary.cross_signal || "Disabled";
  const factors = Array.isArray(summary.signal_factors) ? summary.signal_factors : [];

  let tone = "wait";
  let badge = t("wait");
  let title = currentLanguage === "fa" ? "منتظر ستاپ تمیزتر بمانید" : "Watch for a cleaner setup";
  if (action.toLowerCase().includes("buy")) {
    tone = "buy";
    badge = t("buyBias");
    title = currentLanguage === "fa" ? "ستاپ احتمالی خرید" : "Potential buy setup";
  } else if (action.toLowerCase().includes("sell")) {
    tone = "sell";
    badge = t("sellBias");
    title = currentLanguage === "fa" ? "ستاپ احتمالی فروش" : "Potential sell setup";
  } else if (action.toLowerCase().includes("active watch")) {
    badge = currentLanguage === "fa" ? "رصد فعال" : "Active watch";
    title = currentLanguage === "fa" ? "ستاپ نیاز به تایید دارد" : "Setup needs confirmation";
  }

  const reasons = [];
  if (macd !== "Disabled") {
    reasons.push(currentLanguage === "fa" ? `MACD ${translateValue(macd)} است` : `MACD is ${macd.toLowerCase()}`);
  }
  if (cross && cross !== "Disabled" && cross !== "None") {
    reasons.push(translateValue(cross));
  }
  if (rsi !== "Disabled") {
    reasons.push(currentLanguage === "fa" ? `RSI ${translateValue(rsi)} است` : `RSI is ${rsi.toLowerCase()}`);
  }
  if (summary.risk_level) {
    reasons.push(currentLanguage === "fa" ? `ریسک ${translateValue(summary.risk_level)} است` : `risk is ${String(summary.risk_level).toLowerCase()}`);
  }
  if (Number.isFinite(Number(summary.buy_score)) && Number.isFinite(Number(summary.sell_score))) {
    reasons.push(
      currentLanguage === "fa"
        ? `امتیاز خرید ${Number(summary.buy_score).toFixed(1)} در برابر فروش ${Number(summary.sell_score).toFixed(1)}`
        : `buy score ${Number(summary.buy_score).toFixed(1)} vs sell score ${Number(summary.sell_score).toFixed(1)}`
    );
  }
  const factorText = factors.length ? factors.map(translateFactorText).join(" ") : "";

  return {
    badge,
    confidence,
    reason: reasons.length ? reasons.join(currentLanguage === "fa" ? "، " : ", ") : t("setupEmpty"),
    title,
    tone,
    explanation:
      currentLanguage === "fa"
        ? [
            `این ستاپ به عنوان ${badge} نمایش داده شده چون اندیکاتورهای فعال به یک جهت کلی تبدیل شده‌اند.`,
            macd !== "Disabled" ? `MACD مومنتوم ${translateValue(macd)} نشان می‌دهد.` : "MACD غیرفعال است و وزن مومنتوم کمتر است.",
            rsi !== "Disabled" ? `RSI در وضعیت ${translateValue(rsi)} است و به تشخیص شرایط کشیده یا خنثی کمک می‌کند.` : "RSI غیرفعال است.",
            factorText ? `عوامل اصلی: ${factorText}` : "",
            `اعتماد ${confidence}% است؛ این فقط ابزار برنامه‌ریزی است، نه سیگنال قطعی.`,
          ].join(" ")
        : [
            `The setup is marked as ${badge.toLowerCase()} because the active indicators are being combined into one bias.`,
            macd !== "Disabled" ? `MACD shows ${macd.toLowerCase()} momentum.` : "MACD is disabled, so momentum has less weight.",
            rsi !== "Disabled" ? `RSI is ${rsi.toLowerCase()}, which helps spot stretched or neutral price conditions.` : "RSI is disabled, so overbought/oversold filtering is not used.",
            factorText ? `Main factors: ${factorText}` : "",
            `Confidence is ${confidence}%, so this should be treated as a planning aid, not a guaranteed signal.`,
          ].join(" "),
  };
}

function updateSetupCard(summary) {
  const card = document.getElementById("setupCard");
  if (!card) {
    return;
  }

  const setup = buildSetup(summary);
  card.classList.remove("setup-buy", "setup-sell", "setup-wait");
  card.classList.add(`setup-${setup.tone}`);
  document.getElementById("setupTitle").textContent = setup.title;
  document.getElementById("setupBadge").textContent = setup.badge;
  document.getElementById("setupReason").textContent = setup.reason;
  document.getElementById("setupStrengthText").textContent = `${setup.confidence}%`;
  document.getElementById("setupStrengthBar").style.width = `${setup.confidence}%`;
  latestSetupExplanation = setup.explanation;
  if (explainText && !explainText.classList.contains("hidden")) {
    explainText.textContent = latestSetupExplanation;
  }
}

function updateTradePlan(summary, prices) {
  const entryEl = document.getElementById("planEntry");
  const stopEl = document.getElementById("planStop");
  const targetEl = document.getElementById("planTarget");
  const rrEl = document.getElementById("planRr");
  const noteEl = document.getElementById("planNote");
  if (!entryEl || !stopEl || !targetEl || !rrEl || !noteEl) {
    return;
  }

  const direction = getSetupDirection(summary.action_bias);
  const latest = Number(summary.latest_price);
  if (!latest || direction === "wait") {
    entryEl.textContent = "-";
    stopEl.textContent = "-";
    targetEl.textContent = "-";
    rrEl.textContent = "-";
    noteEl.textContent = t("noTradePlan");
    return;
  }

  const pipSize = getPipSize();
  const move = averageMove(prices);
  const stopDistance = Math.max(move * 2, pipSize * 8);
  const targetDistance = stopDistance * 1.5;
  const stop = direction === "buy" ? latest - stopDistance : latest + stopDistance;
  const target = direction === "buy" ? latest + targetDistance : latest - targetDistance;
  const stopPips = stopDistance / pipSize;

  entryEl.textContent = formatNum(latest, 5);
  stopEl.textContent = formatNum(stop, 5);
  targetEl.textContent = formatNum(target, 5);
  rrEl.textContent = "1:1.5";
  noteEl.textContent = t("planNote");

  const stopInput = document.getElementById("stopPips");
  if (stopInput) {
    stopInput.value = stopPips.toFixed(1);
    updateRiskCalculator();
  }
}

function updateRiskCalculator() {
  const balance = Number(document.getElementById("accountBalance")?.value || 0);
  const riskPercent = Number(document.getElementById("riskPercent")?.value || 0);
  const stopPips = Number(document.getElementById("stopPips")?.value || 0);
  const pipValue = Number(document.getElementById("pipValue")?.value || 0);
  const lotEl = document.getElementById("riskLotSize");
  const amountEl = document.getElementById("riskAmount");
  if (!lotEl || !amountEl) {
    return;
  }

  const riskAmount = balance * (riskPercent / 100);
  if (riskAmount <= 0 || stopPips <= 0 || pipValue <= 0) {
    lotEl.textContent = "-";
    amountEl.textContent = "-";
    return;
  }

  const lots = riskAmount / (stopPips * pipValue);
  lotEl.textContent = `${lots.toFixed(2)} ${t("lots")}`;
  amountEl.textContent = `$${riskAmount.toFixed(2)} ${t("atRisk")}`;
}

function applyStrategyPreset(name) {
  const preset = strategyPresets[name];
  if (!preset) {
    return;
  }

  const fields = {
    symbol: preset.symbol,
    interval: preset.interval,
    outputsize: preset.outputsize,
    rsiPeriod: preset.rsi,
    macdShort: preset.macdShort,
    macdLong: preset.macdLong,
    macdSignal: preset.macdSignal,
    tradeProfile: preset.aiProfile,
    customMaxHoldingMinutes: preset.holding,
    holdingBars: preset.holdingBars,
    feeBps: preset.feeBps,
    mt5AtrStop: preset.atrStopMultiple,
    mt5RewardRisk: preset.rewardRisk,
    mt5RiskPercent: preset.riskPercent,
    mt5MinStrength: preset.minimumStrength,
    mt5MaxSpread: preset.maximumSpreadBps,
    mt5MaxVolume: preset.maximumVolume,
    mt5DailyLoss: preset.maximumDailyLoss,
    mt5DailyTradesLimit: preset.maximumDailyTrades,
    mt5AiConfidence: preset.minimumAiConfidence,
  };

  Object.entries(fields).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element && value != null) {
      element.value = value;
    }
  });
  observedCandleStartMs = null;
  updateCandleClock();
}

function updateCandleClock() {
  const remainingEl = document.getElementById("candleClockRemaining");
  const timeframeEl = document.getElementById("candleClockTimeframe");
  const closeEl = document.getElementById("candleClockClose");
  const progressEl = document.getElementById("candleClockProgress");
  const phaseEl = document.getElementById("candleClockPhase");
  const labelEl = document.getElementById("candleClockLabel");
  if (!remainingEl || !timeframeEl || !closeEl || !progressEl || !phaseEl || !labelEl) return;

  const interval = document.getElementById("interval")?.value || "4h";
  const minutesByInterval = {
    "1min": 1, "5min": 5, "15min": 15, "30min": 30,
    "1h": 60, "4h": 240, "1day": 1440,
  };
  const durationMs = (minutesByInterval[interval] || 240) * 60 * 1000;
  const browserNow = Date.now();
  const now = browserNow + mt5ServerClockOffsetMs;
  const candleStart = Math.floor(now / durationMs) * durationMs;
  const candleClose = candleStart + durationMs;
  const remainingSeconds = Math.max(0, Math.ceil((candleClose - now) / 1000));
  const hours = Math.floor(remainingSeconds / 3600);
  const minutes = Math.floor((remainingSeconds % 3600) / 60);
  const seconds = remainingSeconds % 60;
  const elapsedRatio = Math.min(1, Math.max(0, (now - candleStart) / durationMs));
  const hourMs = 60 * 60 * 1000;
  const demoHourSlotStart = Math.floor(now / hourMs) * hourMs;
  const demoHourIndex = Math.min(3, Math.max(0, Math.floor((now - candleStart) / hourMs)));
  currentDemoHourSlot = String(Math.floor(demoHourSlotStart / hourMs));
  currentDemoHourVolume = [0.01, 0.02, 0.03, 0.04][demoHourIndex] || 0.01;
  const phase = elapsedRatio < 0.25 ? "start" : (elapsedRatio < 0.75 ? "middle" : "end");
  const names = {
    "1min": "M1", "5min": "M5", "15min": "M15", "30min": "M30",
    "1h": "H1", "4h": "H4", "1day": "D1",
  };
  const phaseText = currentLanguage === "fa"
    ? { start: "ابتدای کندل", middle: "میانه کندل", end: "انتهای کندل" }[phase]
    : { start: "Early candle", middle: "Middle of candle", end: "Late candle" }[phase];
  const locale = currentLanguage === "fa" ? "fa-IR" : "en-US";

  timeframeEl.textContent = names[interval] || interval.toUpperCase();
  labelEl.textContent = currentLanguage === "fa"
    ? "زمان باقی‌مانده تا بسته‌شدن کندل"
    : "Time until candle close";
  remainingEl.textContent = [hours, minutes, seconds]
    .map(value => String(value).padStart(2, "0")).join(":");
  const localCandleClose = candleClose - mt5ServerClockOffsetMs;
  closeEl.textContent = `${currentLanguage === "fa" ? "بسته‌شدن:" : "Closes:"} ${new Date(localCandleClose).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}`;
  progressEl.style.width = `${(elapsedRatio * 100).toFixed(2)}%`;
  const hourlyLabSuffix = document.getElementById("demoLabMode")?.checked && interval === "4h"
    ? (currentLanguage === "fa" ? ` · حجم این ساعت ${currentDemoHourVolume.toFixed(2)} لات` : ` · this hour ${currentDemoHourVolume.toFixed(2)} lot`)
    : "";
  phaseEl.textContent = `${phaseText} · ${Math.round(elapsedRatio * 100).toLocaleString(locale)}% ${currentLanguage === "fa" ? "سپری شده" : "elapsed"}${hourlyLabSuffix}`;

  if (observedCandleStartMs == null) {
    observedCandleStartMs = candleStart;
  } else if (candleStart > observedCandleStartMs) {
    observedCandleStartMs = candleStart;
    if (!document.getElementById("demoLabMode")?.checked && document.getElementById("autoCandleAnalysis")?.checked && !autoCandleCyclePending) {
      autoCandleCyclePending = true;
      setAutoCandleStatus(currentLanguage === "fa"
        ? "کندل بسته شد؛ چند ثانیه تا دریافت داده بسته‌شده جدید…"
        : "Candle closed; waiting briefly for the new closed bar…");
      setTimeout(runAutoCandleCycle, 7000);
    }
  }
  if (observedDemoHourSlotMs == null) {
    observedDemoHourSlotMs = demoHourSlotStart;
  } else if (demoHourSlotStart > observedDemoHourSlotMs) {
    observedDemoHourSlotMs = demoHourSlotStart;
    const hourlyGoldLab = interval === "4h" && document.getElementById("demoLabMode")?.checked;
    if (hourlyGoldLab && document.getElementById("autoCandleAnalysis")?.checked && !autoCandleCyclePending) {
      autoCandleCyclePending = true;
      setAutoCandleStatus(currentLanguage === "fa"
        ? `اسلات ساعتی جدید؛ آماده تحلیل H4 با حجم ${currentDemoHourVolume.toFixed(2)} لات…`
        : `New hourly slot; preparing H4 analysis at ${currentDemoHourVolume.toFixed(2)} lot…`);
      setTimeout(runAutoCandleCycle, 7000);
    }
  }
}

function setAutoCandleStatus(message) {
  const status = document.getElementById("autoCandleStatus");
  if (status) status.textContent = message;
}

async function runAutoCandleCycle() {
  try {
    if (!document.getElementById("autoCandleAnalysis")?.checked) return;
    setAutoCandleStatus(currentLanguage === "fa"
      ? "در حال تحلیل خودکار کندل بسته‌شده…"
      : "Analyzing the newly closed candle…");
    const payload = await buildMt5SignalPreview({
      automatic: true,
      demoLabSlot: currentDemoHourSlot,
      demoLabVolume: currentDemoHourVolume,
    });
    if (!payload) {
      setAutoCandleStatus(currentLanguage === "fa"
        ? "تحلیل خودکار ناموفق بود؛ در بسته‌شدن کندل بعدی دوباره تلاش می‌شود."
        : "Automatic analysis failed; it will retry after the next candle.");
      return;
    }
    if (payload.execution_ready && document.getElementById("autoDemoExecution")?.checked) {
      setAutoCandleStatus(currentLanguage === "fa"
        ? "همه فیلترها پاس شدند؛ در حال ارسال سفارش محافظت‌شده DEMO…"
        : "All gates passed; sending the protected DEMO order…");
      await executeDemoOrder({ automatic: true });
      return;
    }
    const signal = payload.signal?.display_signal || payload.signal?.signal || "HOLD";
    setAutoCandleStatus(currentLanguage === "fa"
      ? `تحلیل انجام شد: ${signal}؛ سفارشی ارسال نشد.`
      : `Analysis completed: ${signal}; no order was sent.`);
  } finally {
    autoCandleCyclePending = false;
  }
}

function updateMarketSession() {
  const sessionEl = document.getElementById("sessionName");
  const pill = document.getElementById("sessionPill");
  if (!sessionEl || !pill) {
    return;
  }

  const hour = new Date().getUTCHours();
  let sessionKey = "offPeak";
  let tone = "quiet";
  if (hour >= 13 && hour < 16) {
    sessionKey = "overlap";
    tone = "hot";
  } else if (hour >= 7 && hour < 16) {
    sessionKey = "london";
    tone = "active";
  } else if (hour >= 13 && hour < 22) {
    sessionKey = "newYork";
    tone = "active";
  } else if (hour >= 0 && hour < 8) {
    sessionKey = "asia";
    tone = "quiet";
  }
  const sessionNames = {
    en: {
      offPeak: "Off-peak",
      overlap: "London/New York overlap",
      london: "London",
      newYork: "New York",
      asia: "Asia",
    },
    fa: {
      offPeak: "کم‌حجم",
      overlap: "هم‌پوشانی لندن/نیویورک",
      london: "لندن",
      newYork: "نیویورک",
      asia: "آسیا",
    },
  };

  pill.classList.remove("session-active", "session-hot", "session-quiet");
  pill.classList.add(`session-${tone}`);
  sessionEl.textContent = sessionNames[currentLanguage]?.[sessionKey] || sessionNames.en[sessionKey];
}

function renderPriceChart(prices) {
  const ctx = document.getElementById("priceChart").getContext("2d");
  if (priceChart) {
    priceChart.destroy();
  }

  priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: buildLabels(prices.length),
      datasets: [
        {
          label: "Close Price",
          data: prices,
          borderColor: "#38bdf8",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
        },
      ],
    },
    options: { responsive: true },
  });
}

function renderRsiChart(data) {
  const ctx = document.getElementById("rsiChart").getContext("2d");
  if (rsiChart) {
    rsiChart.destroy();
  }

  rsiChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: buildLabels(data.length),
      datasets: [
        {
          label: "RSI",
          data,
          borderColor: "#2dd4bf",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      scales: { y: { min: 0, max: 100 } },
    },
  });
}

function renderMacdChart(macd) {
  const ctx = document.getElementById("macdChart").getContext("2d");
  if (macdChart) {
    macdChart.destroy();
  }

  const labels = buildLabels(macd["MACD"].length);

  macdChart = new Chart(ctx, {
    data: {
      labels,
      datasets: [
        {
          type: "line",
          label: "MACD",
          data: macd["MACD"],
          borderColor: "#2dd4bf",
          pointRadius: 0,
          tension: 0.2,
        },
        {
          type: "line",
          label: "Signal",
          data: macd["Signal Line"],
          borderColor: "#f59e0b",
          pointRadius: 0,
          tension: 0.2,
        },
        {
          type: "bar",
          label: "Histogram",
          data: macd["Histogram"],
          backgroundColor: "rgba(56, 189, 248, 0.45)",
        },
      ],
    },
    options: { responsive: true },
  });
}

function updateJournalDefaults(summary) {
  const symbolInput = document.getElementById("journalSymbol");
  const directionInput = document.getElementById("journalDirection");
  const entryInput = document.getElementById("journalEntry");
  const stopInput = document.getElementById("journalStop");
  const targetInput = document.getElementById("journalTarget");
  const exitInput = document.getElementById("journalExit");
  if (!symbolInput || !entryInput || !stopInput || !targetInput) return;

  const latest = Number(summary?.latest_price);
  const plannedEntry = Number(document.getElementById("planEntry")?.textContent);
  const plannedStop = Number(document.getElementById("planStop")?.textContent);
  const plannedTarget = Number(document.getElementById("planTarget")?.textContent);

  symbolInput.value = document.getElementById("symbol")?.value || "EUR/USD";
  if (directionInput) {
    directionInput.value = getSetupDirection(summary?.action_bias) === "sell" ? "sell" : "buy";
  }
  entryInput.value = Number.isFinite(plannedEntry) && plannedEntry > 0
    ? plannedEntry.toFixed(5)
    : (Number.isFinite(latest) && latest > 0 ? latest.toFixed(5) : "1.10000");
  if (Number.isFinite(plannedStop) && plannedStop > 0) stopInput.value = plannedStop.toFixed(5);
  if (Number.isFinite(plannedTarget) && plannedTarget > 0) targetInput.value = plannedTarget.toFixed(5);
  if (exitInput) exitInput.value = "";
}

function updateMentorMessage(summary) {
  const message = document.getElementById("mentorMessage");
  if (!message || !summary) return;
  const action = String(summary.action_bias || "Wait");
  const strength = Number(summary.signal_strength || summary.confidence || 0);
  const alignment = summary.timeframe_alignment?.alignment || "mixed";
  const highRisk = summary.risk_level === "High" || action === "Wait";

  if (currentLanguage === "fa") {
    if (highRisk) {
      message.textContent = `فعلاً عجله نکن. امتیاز هم‌جهتی ${strength} از ۱۰۰ است و شواهد برای ورود کافی نیستند؛ اول منتظر جهت روشن‌تر و حد ضرر معتبر بمان.`;
    } else if (alignment === "mixed") {
      message.textContent = `ستاپ ${action.toLowerCase().includes("sell") ? "فروش" : "خرید"} دیده می‌شود، اما تایم‌فریم‌ها هم‌نظر نیستند. حجم را سبک نگه دار و فقط با تأیید بیشتر وارد شو.`;
    } else {
      message.textContent = `شواهد فنی با امتیاز ${strength} از ۱۰۰ هم‌جهت شده‌اند. قبل از ورود، فاصله حد ضرر و مبلغ واقعی در معرض ریسک را دوباره بررسی کن.`;
    }
  } else if (highRisk) {
    message.textContent = `Do not rush. Indicator agreement is ${strength}/100 and the evidence is not strong enough for entry. Wait for a clearer direction and a valid stop.`;
  } else if (alignment === "mixed") {
    message.textContent = `A ${action.toLowerCase()} setup is visible, but the timeframes disagree. Keep size small and wait for more confirmation.`;
  } else {
    message.textContent = `Technical evidence is aligned at ${strength}/100. Before entry, verify the stop distance and the actual amount at risk.`;
  }
}

function updateDecision(summary) {
  updateSetupCard(summary);
  updateTradePlan(summary, latestComputed?.prices || []);
  updateJournalDefaults(summary);
  updateMentorMessage(summary);
  document.getElementById("mPrice").textContent = formatNum(summary.latest_price, 5);
  document.getElementById("mRsi").textContent = formatNum(summary.latest_rsi, 2);
  document.getElementById("mRsiState").textContent = translateValue(summary.rsi_state);
  document.getElementById("mMacdBias").textContent = translateValue(summary.macd_bias);
  document.getElementById("mCross").textContent = translateValue(summary.cross_signal);
  document.getElementById("mAction").textContent = translateValue(summary.action_bias);
  document.getElementById("mConfidence").textContent = summary.signal_strength ? `${summary.signal_strength}/100` : "-";
  document.getElementById("mRisk").textContent = translateValue(summary.risk_level);
  document.getElementById("mAtr").textContent = summary.latest_atr
    ? `${formatNum(summary.latest_atr, 6)} (${summary.volatility_source || "ATR"})`
    : "-";
  const alignment = summary.timeframe_alignment || {};
  document.getElementById("mAlignment").textContent =
    `${alignment.short || "-"} / ${alignment.medium || "-"} / ${alignment.higher || "-"}`;
  document.getElementById("systemNote").textContent = translateValue(summary.note);
}

function listItems(items) {
  return Array.isArray(items) ? items.map((x) => `<li>${x}</li>`).join("") : "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function aiTone(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("buy") || normalized.includes("bull")) {
    return "buy";
  }
  if (normalized.includes("sell") || normalized.includes("bear")) {
    return "sell";
  }
  if (normalized.includes("no") || normalized.includes("wait")) {
    return "wait";
  }
  return "neutral";
}

function renderAiList(title, items, emptyText = "-") {
  const cleanItems = Array.isArray(items) ? items.filter(Boolean) : [];
  return `
    <section class="ai-list-card">
      <h3>${escapeHtml(title)}</h3>
      ${
        cleanItems.length
          ? `<ul>${cleanItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
          : `<p class="muted">${escapeHtml(emptyText)}</p>`
      }
    </section>
  `;
}

function renderAiResult(payload) {
  latestAiPayload = payload;
  const resultBox = document.getElementById("aiResult");
  const a = payload.analysis || {};
  const labels = uiText[currentLanguage].aiLabels;
  const confidence = Number.isFinite(Number(a.confidence)) ? Math.max(0, Math.min(100, Number(a.confidence))) : 0;
  const tone = aiTone(`${a.action_bias || ""} ${a.market_state || ""}`);
  const holdingText = a.holding_time_minutes ? `${escapeHtml(a.holding_time_minutes)} ${t("minute")}` : "-";
  const macro = payload.macro_context || {};
  const macroEvents = Array.isArray(macro.events) ? macro.events : [];
  const macroTitle = currentLanguage === "fa" ? "تقویم اقتصادی آمریکا" : "US economic calendar";
  const macroUnavailable = currentLanguage === "fa"
    ? "تقویم اقتصادی در این تحلیل در دسترس نبود؛ تحلیل تکنیکال ادامه یافت."
    : "The economic calendar was unavailable; technical analysis continued.";
  const macroPrecision = currentLanguage === "fa"
    ? "زمان دقیق انتشار در این منبع موجود نیست؛ تاریخ‌ها فقط هشدار ریسک روزانه‌اند."
    : "Exact release times are unavailable; dates are daily risk warnings only.";
  const macroHtml = macro.available
    ? `<section class="ai-list-card">
        <h3>${escapeHtml(macroTitle)}</h3>
        ${macroEvents.length
          ? `<ul>${macroEvents.map((event) => `<li><b>${escapeHtml(event.release_date)}</b> · ${escapeHtml(event.name)}</li>`).join("")}</ul>`
          : `<p class="muted">${escapeHtml(currentLanguage === "fa" ? "در هفت روز آینده رویداد مهمی از فهرست منتخب پیدا نشد." : "No selected major release was found in the next seven days.")}</p>`}
        <p class="muted">${escapeHtml(macroPrecision)}</p>
      </section>`
    : `<section class="ai-list-card"><h3>${escapeHtml(macroTitle)}</h3><p class="muted">${escapeHtml(macroUnavailable)}</p></section>`;

  resultBox.innerHTML = `
    <div class="ai-summary ai-${tone}">
      <div>
        <span class="setup-label">${escapeHtml(labels.market_state)}</span>
        <h3>${escapeHtml(a.market_state || "-")}</h3>
        <p>${escapeHtml(a.liquidity_note || "-")}</p>
      </div>
      <span class="ai-bias">${escapeHtml(a.action_bias || "-")}</span>
    </div>

    <div class="ai-metrics">
      <div class="metric"><span>${escapeHtml(labels.profile_used)}</span><strong>${escapeHtml(a.profile_used || "-")}</strong></div>
      <div class="metric"><span>${escapeHtml(labels.confidence)}</span><strong>${confidence ? `${confidence}%` : "-"}</strong></div>
      <div class="metric"><span>${escapeHtml(labels.execution_type)}</span><strong>${escapeHtml(a.execution_type || "-")}</strong></div>
      <div class="metric"><span>${escapeHtml(labels.holding_time_minutes)}</span><strong>${holdingText}</strong></div>
    </div>

    <div class="ai-confidence">
      <span style="width: ${confidence}%"></span>
    </div>

    <div class="ai-trade-grid">
      <section class="ai-trade-card">
        <span>${escapeHtml(labels.entry_idea)}</span>
        <strong>${escapeHtml(a.entry_idea || "-")}</strong>
      </section>
      <section class="ai-trade-card">
        <span>${escapeHtml(labels.stop_loss_idea)}</span>
        <strong>${escapeHtml(a.stop_loss_idea || "-")}</strong>
      </section>
      <section class="ai-trade-card">
        <span>${escapeHtml(labels.take_profit_idea)}</span>
        <strong>${escapeHtml(a.take_profit_idea || "-")}</strong>
      </section>
    </div>

    <div class="ai-detail-grid">
      ${renderAiList(labels.why, a.why)}
      ${renderAiList(labels.risk_warnings, a.risk_warnings)}
      ${Array.isArray(a.nds_checklist) && a.nds_checklist.length ? renderAiList(labels.nds_checklist, a.nds_checklist) : ""}
      ${macroHtml}
    </div>

    <p class="ai-disclaimer">${escapeHtml(payload.disclaimer || "")}</p>
  `;

  resultBox.classList.remove("hidden");
}

function setAiStatus(message, showProgress) {
  if (message) {
    aiStatus.textContent = message;
    aiStatus.classList.remove("hidden");
  } else {
    aiStatus.textContent = "";
    aiStatus.classList.add("hidden");
  }

  aiProgress.classList.toggle("hidden", !showProgress);
}

function metricCard(label, value) {
  return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? "-")}</strong></div>`;
}

function renderBacktest(result) {
  latestBacktestResult = result;
  const box = document.getElementById("backtestResult");
  if (!box) return;
  const extraMetrics = result.engine === "ohlc_next_bar_conservative" ? [
    metricCard(currentLanguage === "fa" ? "خرید و نگهداری" : "Buy & hold", `${result.buy_hold_pct}%`),
    metricCard(currentLanguage === "fa" ? "میانگین برد" : "Average win", result.average_win_pct == null ? "-" : `${result.average_win_pct}%`),
    metricCard(currentLanguage === "fa" ? "میانگین باخت" : "Average loss", result.average_loss_pct == null ? "-" : `${result.average_loss_pct}%`),
  ] : [];
  const tradeRows = Array.isArray(result.trades) && result.trades.length ? `
    <div class="backtest-trades">
      <h3>${currentLanguage === "fa" ? "معاملات شبیه‌سازی‌شده" : "Simulated trades"}</h3>
      ${result.trades.slice(-30).map((trade) => `
        <article class="record-row">
          <strong>${escapeHtml(trade.direction)} · ${escapeHtml(trade.exit_reason || trade.outcome)}</strong>
          <span>${escapeHtml(trade.pnl_pct)}%</span>
          <small>${escapeHtml(trade.entry_time || trade.entry_index)} → ${escapeHtml(trade.exit_time || trade.exit_index)} · ${escapeHtml(trade.entry)} → ${escapeHtml(trade.exit)}</small>
        </article>`).join("")}
    </div>` : "";
  box.innerHTML = [
    metricCard(t("backtest.trades"), result.trade_count),
    metricCard(t("backtest.winRate"), result.win_rate == null ? "-" : `${result.win_rate}%`),
    metricCard(t("backtest.totalReturn"), `${result.total_return_pct}%`),
    metricCard(t("backtest.profitFactor"), result.profit_factor),
    metricCard(t("backtest.expectancy"), result.expectancy_pct == null ? "-" : `${result.expectancy_pct}%`),
    metricCard(t("backtest.drawdown"), `${result.max_drawdown_pct}%`),
    metricCard(t("backtest.sharpe"), result.sharpe),
    ...extraMetrics,
    `<p class="backtest-warning">${escapeHtml(
      result.trade_count ? t("backtest.warning") : t("backtest.noTrades")
    )}${result.halted_reason ? ` · ${escapeHtml(result.halted_reason)}` : ""}</p>`,
    tradeRows,
  ].join("");
  box.classList.remove("hidden");
}

async function loadHistory() {
  const list = document.getElementById("historyList");
  if (!list) return;
  try {
    const { response, data } = await apiFetch("history");
    if (!response.ok) throw new Error(data.error || "History failed");
    const items = Array.isArray(data.items) ? data.items : [];
    const automated = Array.isArray(data.automated_signals) ? data.automated_signals : [];
    const automatedHtml = automated.map((item) => {
      const details = item.details || {};
      const plan = details.risk_plan || {};
      const reasons = Array.isArray(details.reasons) ? details.reasons : [];
      const outcome = item.trade_status || "open";
      const realized = item.realized_net == null ? "-" : `${Number(item.realized_net).toFixed(2)} USD`;
      return `
        <article class="record-row automated-record">
          <strong>${escapeHtml(item.signal)} · ${escapeHtml(item.symbol)} · ${escapeHtml(item.interval)}</strong>
          <span>${currentLanguage === "fa" ? "معامله" : "Trade"}: ${escapeHtml(outcome)} · P/L ${escapeHtml(realized)}</span>
          <small>
            Entry: ${escapeHtml(item.entry_price ?? plan.entry ?? "-")} ·
            SL: ${escapeHtml(item.stop_loss ?? plan.stop_loss ?? "-")} ·
            TP: ${escapeHtml(item.take_profit ?? plan.take_profit ?? "-")} ·
            Order: ${escapeHtml(item.order_ticket ?? "-")}
          </small>
          ${reasons.length ? `<small>${reasons.map(escapeHtml).join(" · ")}</small>` : ""}
          <small>${escapeHtml(new Date(item.created_at).toLocaleString())}</small>
        </article>`;
    }).join("");
    const manualHtml = items.map((item) => `
          <article class="record-row">
            <strong>${escapeHtml(item.symbol)} · ${escapeHtml(item.interval)}</strong>
            <span>${escapeHtml(item.action_bias)} · ${escapeHtml(item.signal_strength)}/100</span>
            <small>${escapeHtml(new Date(item.created_at).toLocaleString())}</small>
          </article>`).join("");
    list.innerHTML = automatedHtml || manualHtml
      ? `${automatedHtml}${manualHtml}`
      : `<p class="muted">No saved analysis yet.</p>`;
  } catch {
    list.innerHTML = `<p class="error">Could not load analysis history.</p>`;
  }
}

async function loadJournal() {
  const list = document.getElementById("journalList");
  if (!list) return;
  try {
    const { response, data } = await apiFetch("journal");
    if (!response.ok) throw new Error(data.error || "Journal failed");
    const items = Array.isArray(data.items) ? data.items : [];
    list.innerHTML = items.length
      ? items.map((item) => `
          <article class="record-row">
            <strong>${escapeHtml(item.symbol)} · ${escapeHtml(item.direction)}</strong>
            <span>${escapeHtml(item.status)}</span>
            <small>
              Entry: ${escapeHtml(item.entry_price ?? "-")} ·
              Stop: ${escapeHtml(item.stop_loss ?? "-")} ·
              Target: ${escapeHtml(item.take_profit ?? "-")} ·
              Exit: ${escapeHtml(item.exit_price ?? "-")} ·
              ${escapeHtml(item.notes || "")}
            </small>
          </article>`).join("")
      : `<p class="muted">No journal entries yet.</p>`;
  } catch {
    list.innerHTML = `<p class="error">Could not load trading journal.</p>`;
  }
}

const backtestBtn = document.getElementById("backtestBtn");
if (backtestBtn) {
  backtestBtn.addEventListener("click", async () => {
    hideError();
    const prices = parsePrices(document.getElementById("prices").value);
    if (prices.length < 50 || prices.some((value) => Number.isNaN(value))) {
      showError(t("backtest.needData"));
      return;
    }
    backtestBtn.disabled = true;
    try {
      const payload = {
        prices,
        opens: latestMarketData.opens,
        highs: latestMarketData.highs,
        lows: latestMarketData.lows,
        timestamps: latestMarketData.labels,
        rsi_period: Number(document.getElementById("rsiPeriod").value),
        macd_short_period: Number(document.getElementById("macdShort").value),
        macd_long_period: Number(document.getElementById("macdLong").value),
        macd_signal_period: Number(document.getElementById("macdSignal").value),
        holding_bars: Number(document.getElementById("holdingBars").value),
        fee_bps: Number(document.getElementById("feeBps").value),
        risk_percent: Number(document.getElementById("mt5RiskPercent")?.value || 0.5),
        atr_stop_multiple: Number(document.getElementById("mt5AtrStop")?.value || 1.5),
        reward_risk: Number(document.getElementById("mt5RewardRisk")?.value || 2),
        slippage_bps_per_side: 0.2,
      };
      const { response, data } = await apiFetch("backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        showError(data.error || t("backtest.failed"));
        return;
      }
      renderBacktest(data);
    } catch {
      showError(t("backtest.connection"));
    } finally {
      backtestBtn.disabled = false;
    }
  });
}

const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");
if (refreshHistoryBtn) refreshHistoryBtn.addEventListener("click", loadHistory);

async function loadMultiAssetResearch() {
  const box = document.getElementById("multiAssetResearch");
  if (!box) return;
  try {
    const { response, data } = await apiFetch("research/multi-asset");
    if (!response.ok || !data.ok) throw new Error(data.error || "Research report failed.");
    const cards = [];
    for (const [timeframe, report] of Object.entries(data.reports || {})) {
      for (const item of report.markets || []) {
        const test = item.test || {};
        const status = item.qualified ? "QUALIFIED" : "RESEARCH ONLY";
        cards.push(`<article class="record-item">
          <strong>${escapeHtml(item.symbol || "-")} · ${escapeHtml(timeframe)} · ${escapeHtml(status)}</strong>
          <small>${escapeHtml(item.strategy_family || "-")} · trades ${escapeHtml(test.trade_count ?? 0)} · win ${escapeHtml(test.win_rate ?? "-")}% · return ${escapeHtml(test.total_return_pct ?? "-")}% · PF ${escapeHtml(test.profit_factor ?? "-")}</small>
        </article>`);
      }
    }
    box.innerHTML = cards.join("") || `<p class="muted">No research report is available.</p>`;
  } catch (error) {
    box.innerHTML = `<p class="error">${escapeHtml(error?.message || "Could not load research results.")}</p>`;
  }
}

document.getElementById("multiAssetRefreshBtn")?.addEventListener("click", loadMultiAssetResearch);
loadMultiAssetResearch();

async function runFastValidation() {
  const button = document.getElementById("fastValidationBtn");
  const box = document.getElementById("fastValidationResult");
  if (!button || !box) return;
  button.disabled = true;
  box.innerHTML = `<p class="muted">در حال بازپخش پروفایل‌ها روی ۵۰۰۰ کندل بسته‌شده…</p>`;
  try {
    const { response, data } = await apiFetch("research/fast-validation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candles: 5000 }),
    });
    if (!response.ok || !data.ok) throw new Error(data.error || "اعتبارسنجی اجرا نشد.");
    box.innerHTML = (data.profiles || []).map((item) => {
      const test = item.test || {};
      const stress = item.stress_test || {};
      const status = item.fresh_validation_qualified ? "قبول" : "رد";
      return `<article class="record-item">
        <strong>${escapeHtml(item.symbol || "-")} · ${escapeHtml(item.interval || "-")} · ${status} · امتیاز ${escapeHtml(item.acceptance_score ?? 0)}/10</strong>
        <small>${escapeHtml(item.strategy_family || "-")} · Test ${escapeHtml(test.total_return_pct ?? "-")}% / PF ${escapeHtml(test.profit_factor ?? "-")} · Stress ${escapeHtml(stress.total_return_pct ?? "-")}% / PF ${escapeHtml(stress.profit_factor ?? "-")}</small>
      </article>`;
    }).join("") || `<p class="muted">نتیجه‌ای تولید نشد.</p>`;
  } catch (error) {
    box.innerHTML = `<p class="error">${escapeHtml(error?.message || "اعتبارسنجی اجرا نشد.")}</p>`;
  } finally {
    button.disabled = false;
  }
}

document.getElementById("fastValidationBtn")?.addEventListener("click", runFastValidation);

const journalForm = document.getElementById("journalForm");
if (journalForm) {
  journalForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();
    const payload = {
      symbol: document.getElementById("journalSymbol").value,
      direction: document.getElementById("journalDirection").value,
      entry_price: document.getElementById("journalEntry").value,
      exit_price: document.getElementById("journalExit").value,
      stop_loss: document.getElementById("journalStop").value,
      take_profit: document.getElementById("journalTarget").value,
      status: document.getElementById("journalStatus").value,
      notes: document.getElementById("journalNotes").value,
    };
    try {
      const { response, data } = await apiFetch("journal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        showError(data.error || "Could not save journal entry.");
        return;
      }
      journalForm.reset();
      updateJournalDefaults(latestComputed?.summary || {});
      loadJournal();
    } catch {
      showError("Could not connect to the journal service.");
    }
  });
}

if (fetchLiveBtn) {
  fetchLiveBtn.addEventListener("click", async () => {
    hideError();

    const payload = {
      symbol: document.getElementById("symbol").value,
      interval: document.getElementById("interval").value,
      outputsize: Number(document.getElementById("outputsize").value),
    };

    try {
      const { response, data: result } = await apiFetch("fetch_forex_prices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        showError(result.error || t("fetchError"));
        return;
      }

      document.getElementById("prices").value = result.prices.join(",");
      latestMarketData = {
        highs: result.highs || null,
        lows: result.lows || null,
        labels: result.labels || null,
      };
    } catch {
      showError(t("fetchConnectionError"));
    }
  });
}

if (mt5ConnectBtn) {
  mt5ConnectBtn.addEventListener("click", checkMt5Connection);
}

if (mt5FetchBtn) {
  mt5FetchBtn.addEventListener("click", loadMt5Candles);
}

if (mt5SignalBtn) {
  mt5SignalBtn.addEventListener("click", async () => {
    mt5SignalBtn.textContent = "در حال تحلیل عددی بدون AI…";
    const payload = await buildMt5SignalPreview({ quick: true, noAi: true, defaultVolume: 0.01 });
    if (payload?.execution_ready) {
      document.getElementById("demoExecutionPanel")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    mt5SignalBtn.textContent = "۱) تحلیل عددی استراتژی بدون AI — لات 0.01";
  });
}

if (quickDemoAnalyzeBtn) {
  quickDemoAnalyzeBtn.addEventListener("click", async () => {
    quickDemoAnalyzeBtn.disabled = true;
    quickDemoAnalyzeBtn.textContent = "در حال تحلیل اقتصادی با Gemini…";
    const payload = await buildMt5SignalPreview({ quick: true, primaryReview: true, defaultVolume: 0.05 });
    if (payload?.execution_ready) {
      document.getElementById("demoExecutionPanel")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    quickDemoAnalyzeBtn.disabled = false;
    quickDemoAnalyzeBtn.textContent = "۲) تحلیل با Gemini ارزان — لات 0.05";
  });
}

if (expensiveAiReviewBtn) {
  expensiveAiReviewBtn.addEventListener("click", async () => {
    expensiveAiReviewBtn.disabled = true;
    expensiveAiReviewBtn.textContent = "در حال داوری دستی با Qwen…";
    const payload = await buildMt5SignalPreview({
      quick: true,
      expensiveReview: true,
      defaultVolume: 0.08,
    });
    if (payload?.execution_ready) {
      document.getElementById("demoExecutionPanel")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    expensiveAiReviewBtn.disabled = false;
    expensiveAiReviewBtn.textContent = "۳) داوری دستی با Qwen گران — لات 0.08";
  });
}

document.getElementById("demoExecuteBtn")?.addEventListener("click", executeDemoOrder);

if (
  mt5Card?.dataset.authenticated === "1"
  && ["127.0.0.1", "localhost"].includes(window.location.hostname)
) {
  checkMt5Connection();
}

document.querySelectorAll("input[name='strategyPreset']").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.checked) {
      applyStrategyPreset(input.value);
    }
  });
});

const autoCandleAnalysis = document.getElementById("autoCandleAnalysis");
const autoDemoExecution = document.getElementById("autoDemoExecution");
const demoLabMode = document.getElementById("demoLabMode");
if (demoLabMode) {
  // Experimental trading modes must always be deliberately re-armed.
  demoLabMode.checked = false;
  demoLabMode.addEventListener("change", () => {
    observedDemoHourSlotMs = null;
    setAutoCandleStatus(demoLabMode.checked
      ? (currentLanguage === "fa" ? "آزمایشگاه DEMO فعال شد؛ در هر کندل H4 چهار BUY/SELL ساعتی با حجم‌های 0.01 تا 0.04 ساخته می‌شود." : "DEMO LAB armed; four hourly BUY/SELL tests per H4 candle use 0.01 through 0.04 lot.")
      : (currentLanguage === "fa" ? "آزمایشگاه DEMO خاموش شد؛ فقط منطق عادی استراتژی اجرا می‌شود." : "DEMO LAB is off; normal strategy logic applies."));
  });
}
if (autoCandleAnalysis && autoDemoExecution) {
  // Arming is deliberately session-only: reload/close always returns to off.
  autoCandleAnalysis.checked = false;
  autoDemoExecution.checked = false;
  autoDemoExecution.disabled = true;
  autoCandleAnalysis.addEventListener("change", () => {
    autoDemoExecution.disabled = !autoCandleAnalysis.checked;
    if (!autoCandleAnalysis.checked) autoDemoExecution.checked = false;
    observedCandleStartMs = null;
    observedDemoHourSlotMs = null;
    updateCandleClock();
    setAutoCandleStatus(autoCandleAnalysis.checked
      ? (currentLanguage === "fa" ? "تحلیل خودکار فعال است؛ منتظر بسته‌شدن کندل." : "Automatic analysis armed; waiting for candle close.")
      : (currentLanguage === "fa" ? "خاموش؛ با تازه‌سازی صفحه دوباره خاموش می‌شود." : "Off; page refresh always disarms automation."));
  });
  autoDemoExecution.addEventListener("change", () => {
    setAutoCandleStatus(autoDemoExecution.checked
      ? (currentLanguage === "fa" ? "اجرای خودکار DEMO مسلح شد؛ در آزمایشگاه فقط امکان فنی ثبت سفارش بررسی می‌شود." : "Automatic DEMO execution armed; in DEMO LAB only technical order availability is checked.")
      : (currentLanguage === "fa" ? "فقط تحلیل خودکار فعال است؛ سفارش خودکار ارسال نمی‌شود." : "Analysis only; automatic orders are off."));
  });
}

["accountBalance", "riskPercent", "stopPips", "pipValue"].forEach((id) => {
  const input = document.getElementById(id);
  if (input) {
    input.addEventListener("input", updateRiskCalculator);
  }
});

if (explainBtn && explainText) {
  explainBtn.addEventListener("click", () => {
    explainText.textContent = latestSetupExplanation || t("explainFirst");
    explainText.classList.toggle("hidden");
  });
}

document.querySelectorAll("[data-mentor-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    currentMentorMode = button.dataset.mentorMode || "education";
    document.querySelectorAll("[data-mentor-mode]").forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    const seedKey = {
      education: "mentor.educationSeed",
      advice: "mentor.adviceSeed",
      review: "mentor.reviewSeed",
    }[currentMentorMode];
    if (window.tradeaiOpenChat) {
      window.tradeaiOpenChat(t(seedKey));
    }
  });
});

const languageToggle = document.getElementById("languageToggle");
if (languageToggle) {
  languageToggle.addEventListener("click", () => {
    currentLanguage = currentLanguage === "fa" ? "en" : "fa";
    localStorage.setItem("tradeaiLanguage", currentLanguage);
    applyLanguage();
  });
}

applyStrategyPreset("goldDemo");
updateRiskCalculator();
updateMarketSession();
loadHistory();
loadJournal();
const manualPricesInput = document.getElementById("prices");
if (manualPricesInput) {
  manualPricesInput.addEventListener("input", () => {
    latestMarketData = { opens: null, highs: null, lows: null, labels: null, market: null, quality: null };
  });
}
setInterval(updateMarketSession, 60000);
setInterval(updateCandleClock, 1000);

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();

    const prices = parsePrices(document.getElementById("prices").value);
    if (prices.length < 30 || prices.some((v) => Number.isNaN(v))) {
      showError(t("minPrices"));
      return;
    }

    const payload = {
      prices,
      highs: latestMarketData.highs,
      lows: latestMarketData.lows,
      symbol: document.getElementById("symbol").value,
      interval: document.getElementById("interval").value,
      use_rsi: document.getElementById("useRsi").checked,
      use_macd: document.getElementById("useMacd").checked,
      use_macd_long: document.getElementById("useMacdLong").checked,
      use_macd_signal: document.getElementById("useMacdSignal").checked,
      use_tdigm: document.getElementById("useTdigm").checked,
      rsi_period: Number(document.getElementById("rsiPeriod").value),
      macd_short_period: Number(document.getElementById("macdShort").value),
      macd_long_period: Number(document.getElementById("macdLong").value),
      macd_signal_period: Number(document.getElementById("macdSignal").value),
      tdigm_value: Number(document.getElementById("tdigmValue").value),
    };

    try {
      const { response, data: result } = await apiFetch("calculate_indicators", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        showError(result.error || t("calculateError"));
        return;
      }

      latestComputed = result;
      renderPriceChart(result.prices);
      renderRsiChart(result.RSI);
      renderMacdChart(result.MACD);
      updateDecision(result.summary);
      loadHistory();
    } catch {
      showError(t("serverError"));
    }
  });

  ["useRsi", "useMacd", "useMacdLong", "useMacdSignal", "useTdigm"].forEach((id) => {
    document.getElementById(id).addEventListener("change", syncIndicatorInputs);
  });
  syncIndicatorInputs();
}

if (aiAnalyzeBtn) {
  aiAnalyzeBtn.addEventListener("click", async () => {
    hideError();

    if (!latestComputed || !latestComputed.summary) {
      showError(t("analyzeFirst"));
      setAiStatus(t("analyzeFirstStatus"), false);
      return;
    }

    const payload = {
      summary: latestComputed.summary,
      recent_prices: latestComputed.prices,
      symbol: document.getElementById("symbol").value,
      interval: document.getElementById("interval").value,
      trade_profile: document.getElementById("tradeProfile").value,
      custom_max_holding_minutes: Number(document.getElementById("customMaxHoldingMinutes").value),
      language: currentLanguage === "fa" ? "Persian" : "English",
    };

    aiAnalyzeBtn.disabled = true;
    setAiStatus(t("aiSending"), true);

    try {
      const { response, data: result } = await apiFetch("analyze_with_ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      // سهمیه‌ی تحلیلِ رایگان تمام شده → به‌جای خطا، چت‌بات را باز کن تا سوال بپرسد/سفارش دهد
      if (response.status === 402 || (result && (result.quota_exhausted || result.login_required))) {
        const msg = result.error || t("aiError");
        setAiStatus(msg, false);
        if (window.tradeaiOpenChat) {
          window.tradeaiOpenChat(msg);
        } else {
          showError(msg);
        }
        return;
      }

      if (!response.ok) {
        showError(result.error || t("aiError"));
        setAiStatus(result.error || t("aiError"), false);
        return;
      }

      renderAiResult(result);
      setAiStatus(t("aiDone"), false);
    } catch {
      showError(t("aiConnectionError"));
      setAiStatus(t("aiUnavailable"), false);
    } finally {
      aiAnalyzeBtn.disabled = false;
    }
  });
}
