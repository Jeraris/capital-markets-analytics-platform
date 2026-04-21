import axios from "axios";

const http = axios.create({ baseURL: "/api" });

export const api = {
  // Market data
  getAllMarketData:   ()       => http.get("/market-data/").then(r => r.data),
  getSymbol:         (sym)    => http.get(`/market-data/${sym}`).then(r => r.data),
  getPriceHistory:   (sym, d) => http.get(`/market-data/${sym}/history?days=${d}`).then(r => r.data),

  // Trades
  getTrades:         (params) => http.get("/trades/", { params }).then(r => r.data),
  createTrade:       (body)   => http.post("/trades/", body).then(r => r.data),

  // Portfolio analytics
  getPnL:            ()       => http.get("/portfolio/pnl").then(r => r.data),
  getExposure:       ()       => http.get("/portfolio/exposure").then(r => r.data),
  getMovingAverage:  (sym, w) => http.get(`/portfolio/moving-average/${sym}?window=${w}`).then(r => r.data),
};
