import argparse
import json
import webbrowser
from pathlib import Path

import pandas as pd

from analysis_utils import extract_model_name


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = PROJECT_DIR / "bazos_produkty.csv"
DEFAULT_OUTPUT = PROJECT_DIR / "dashboard.html"
PRICE_COLUMN = "Čisté číslo"


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and prepare the scraper's semicolon-delimited CSV."""
    data = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    required_columns = {"Produkt", PRICE_COLUMN}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required column(s): {missing}")

    data[PRICE_COLUMN] = pd.to_numeric(data[PRICE_COLUMN], errors="coerce")
    data = data.dropna(subset=[PRICE_COLUMN]).copy()
    data["Produkt"] = data["Produkt"].fillna("").astype(str)
    data["Model"] = data["Produkt"].apply(extract_model_name)
    data.rename(columns={PRICE_COLUMN: "Price"}, inplace=True)
    return data


def create_dashboard(data: pd.DataFrame, output_path: Path) -> None:
    """Write a standalone, interactive HTML dashboard."""
    records = data[["Produkt", "Model", "Price"]].to_dict(orient="records")
    data_json = json.dumps(records, ensure_ascii=False, allow_nan=False)
    data_json = (
        data_json.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    html = DASHBOARD_TEMPLATE.replace("__LISTINGS_DATA__", data_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


DASHBOARD_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>iPhone Listings Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      color: #172033;
      background: #f3f6fb;
    }
    * { box-sizing: border-box; }
    body { margin: 0; }
    header {
      padding: 30px max(24px, calc((100vw - 1200px) / 2));
      color: white;
      background: linear-gradient(120deg, #172554, #2563eb);
    }
    header h1 { margin: 0 0 8px; font-size: 28px; }
    header p { margin: 0; color: #dbeafe; }
    main { max-width: 1200px; margin: 24px auto; padding: 0 20px 40px; }
    .filters, .card {
      border: 1px solid #e1e7f0;
      border-radius: 14px;
      background: white;
      box-shadow: 0 5px 20px #1725540b;
    }
    .filters {
      display: flex;
      flex-wrap: wrap;
      align-items: end;
      gap: 18px;
      margin-bottom: 18px;
      padding: 18px;
    }
    label { display: grid; gap: 7px; color: #526078; font-size: 13px; }
    select, input, button {
      min-height: 40px;
      padding: 8px 11px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      background: white;
      color: #172033;
      font: inherit;
    }
    select { min-width: 190px; }
    input { width: 145px; }
    button {
      cursor: pointer;
      border-color: #2563eb;
      background: #2563eb;
      color: white;
      font-weight: 600;
    }
    button:hover { background: #1d4ed8; }
    .kpis {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }
    .card { padding: 18px; }
    .kpi-label { color: #64748b; font-size: 13px; }
    .kpi-value { margin-top: 8px; font-size: 24px; font-weight: 700; }
    .charts {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }
    h2 { margin: 0 0 12px; font-size: 17px; }
    .chart { width: 100%; min-height: 260px; overflow: visible; }
    .axis-label { fill: #64748b; font-size: 11px; }
    .grid-line { stroke: #e8edf5; stroke-width: 1; }
    .bar { rx: 4px; }
    .table-heading {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .table-wrap { max-height: 440px; overflow: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { padding: 11px 10px; border-bottom: 1px solid #edf1f6; text-align: left; }
    th { position: sticky; top: 0; background: #f8fafc; color: #526078; }
    td.price { white-space: nowrap; font-variant-numeric: tabular-nums; }
    .muted { color: #64748b; font-size: 13px; }
    @media (max-width: 760px) {
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .charts { grid-template-columns: 1fr; }
      main { padding: 0 12px 28px; }
      header { padding: 24px 18px; }
    }
    @media (max-width: 420px) {
      .kpis { grid-template-columns: 1fr 1fr; gap: 8px; }
      .kpi-value { font-size: 20px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>iPhone Listings Dashboard</h1>
    <p>Bazos.sk asking prices and model popularity</p>
  </header>
  <main>
    <section class="filters" aria-label="Dashboard filters">
      <label>iPhone model
        <select id="model-filter"><option value="">All models</option></select>
      </label>
      <label>Minimum price (€)
        <input id="min-price" type="number" step="1">
      </label>
      <label>Maximum price (€)
        <input id="max-price" type="number" step="1">
      </label>
      <button id="download-button" type="button">Download filtered CSV</button>
    </section>
    <section class="kpis" aria-label="Summary statistics">
      <article class="card"><div class="kpi-label">Listings</div><div class="kpi-value" id="listing-count">—</div></article>
      <article class="card"><div class="kpi-label">Average asking price</div><div class="kpi-value" id="average-price">—</div></article>
      <article class="card"><div class="kpi-label">Median asking price</div><div class="kpi-value" id="median-price">—</div></article>
      <article class="card"><div class="kpi-label">Most listed model</div><div class="kpi-value" id="top-model">—</div></article>
    </section>
    <section class="charts">
      <article class="card"><h2>Price distribution</h2><div class="chart" id="price-chart"></div></article>
      <article class="card"><h2>Average price by model</h2><div class="chart" id="average-chart"></div></article>
    </section>
    <section class="card" style="margin-bottom:18px">
      <h2>Listings by model</h2><div class="chart" id="count-chart"></div>
    </section>
    <section class="card">
      <div class="table-heading">
        <h2>Listings</h2>
        <span class="muted" id="table-status"></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Product</th><th>Model</th><th>Price</th></tr></thead>
          <tbody id="listing-rows"></tbody>
        </table>
      </div>
    </section>
  </main>
  <script>
    "use strict";
    const listings = __LISTINGS_DATA__;
    const euro = new Intl.NumberFormat(undefined, {
      style: "currency", currency: "EUR", maximumFractionDigits: 0
    });
    const modelFilter = document.getElementById("model-filter");
    const minInput = document.getElementById("min-price");
    const maxInput = document.getElementById("max-price");

    function addSvgElement(parent, name, attributes, text) {
      const element = document.createElementNS("http://www.w3.org/2000/svg", name);
      for (const [key, value] of Object.entries(attributes)) {
        element.setAttribute(key, String(value));
      }
      if (text !== undefined) element.textContent = text;
      parent.appendChild(element);
      return element;
    }

    function drawBars(containerId, items, color, formatter) {
      const container = document.getElementById(containerId);
      container.replaceChildren();
      if (!items.length) {
        container.textContent = "No data for this selection.";
        container.className = "chart muted";
        return;
      }
      container.className = "chart";
      const width = 720, height = 270;
      const left = 48, right = 12, top = 16, bottom = 76;
      const plotWidth = width - left - right, plotHeight = height - top - bottom;
      const maximum = Math.max(...items.map(item => item.value), 1);
      const svg = addSvgElement(container, "svg", {
        viewBox: `0 0 ${width} ${height}`, role: "img",
        "aria-label": "Bar chart"
      });
      for (let tick = 0; tick <= 4; tick++) {
        const y = top + plotHeight * tick / 4;
        const value = maximum * (4 - tick) / 4;
        addSvgElement(svg, "line", {
          x1: left, y1: y, x2: width - right, y2: y, class: "grid-line"
        });
        addSvgElement(svg, "text", {
          x: left - 7, y: y + 4, "text-anchor": "end", class: "axis-label"
        }, formatter(value));
      }
      const slot = plotWidth / items.length;
      const barWidth = Math.max(2, Math.min(48, slot * 0.68));
      items.forEach((item, index) => {
        const barHeight = item.value / maximum * plotHeight;
        const x = left + slot * index + (slot - barWidth) / 2;
        const y = top + plotHeight - barHeight;
        const bar = addSvgElement(svg, "rect", {
          x, y, width: barWidth, height: Math.max(0, barHeight),
          fill: color, class: "bar"
        });
        addSvgElement(bar, "title", {}, `${item.label}: ${formatter(item.value)}`);
        const label = item.label.length > 13 ? `${item.label.slice(0, 12)}…` : item.label;
        addSvgElement(svg, "text", {
          x: x + barWidth / 2, y: top + plotHeight + 16,
          "text-anchor": "end", transform: `rotate(-35 ${x + barWidth / 2} ${top + plotHeight + 16})`,
          class: "axis-label"
        }, label);
      });
    }

    function getFilteredListings() {
      const model = modelFilter.value;
      const minimum = Number(minInput.value);
      const maximum = Number(maxInput.value);
      return listings.filter(item =>
        (!model || item.Model === model) &&
        Number.isFinite(Number(item.Price)) &&
        Number(item.Price) >= minimum &&
        Number(item.Price) <= maximum
      );
    }

    function updateDashboard() {
      const filtered = getFilteredListings();
      document.getElementById("listing-count").textContent = filtered.length.toLocaleString();
      if (!filtered.length) {
        for (const id of ["average-price", "median-price", "top-model"]) {
          document.getElementById(id).textContent = "—";
        }
        drawBars("price-chart", [], "#2563eb", value => String(Math.round(value)));
        drawBars("average-chart", [], "#16a34a", value => euro.format(value));
        drawBars("count-chart", [], "#f97316", value => String(Math.round(value)));
        document.getElementById("listing-rows").replaceChildren();
        document.getElementById("table-status").textContent = "0 matching listings";
        return;
      }

      const prices = filtered.map(item => Number(item.Price)).sort((a, b) => a - b);
      const mean = prices.reduce((sum, price) => sum + price, 0) / prices.length;
      const middle = Math.floor(prices.length / 2);
      const median = prices.length % 2 ? prices[middle] : (prices[middle - 1] + prices[middle]) / 2;
      const modelCounts = new Map();
      const modelPrices = new Map();
      for (const item of filtered) {
        modelCounts.set(item.Model, (modelCounts.get(item.Model) || 0) + 1);
        const group = modelPrices.get(item.Model) || [];
        group.push(Number(item.Price));
        modelPrices.set(item.Model, group);
      }
      const topModel = [...modelCounts.entries()].sort((a, b) => b[1] - a[1])[0][0];
      document.getElementById("average-price").textContent = euro.format(mean);
      document.getElementById("median-price").textContent = euro.format(median);
      document.getElementById("top-model").textContent = topModel;

      const low = Math.min(...prices), high = Math.max(...prices);
      const binCount = Math.min(12, Math.max(1, Math.ceil(Math.sqrt(prices.length))));
      const binWidth = high === low ? 1 : (high - low) / binCount;
      const bins = Array.from({ length: binCount }, (_, index) => ({
        label: euro.format(low + index * binWidth),
        value: 0
      }));
      for (const price of prices) {
        const index = high === low ? 0 : Math.min(binCount - 1, Math.floor((price - low) / binWidth));
        bins[index].value++;
      }
      drawBars("price-chart", bins, "#2563eb", value => String(Math.round(value)));
      drawBars(
        "average-chart",
        [...modelPrices.entries()]
          .map(([label, values]) => ({
            label, value: values.reduce((sum, price) => sum + price, 0) / values.length
          }))
          .sort((a, b) => b.value - a.value)
          .slice(0, 10),
        "#16a34a",
        value => euro.format(value)
      );
      drawBars(
        "count-chart",
        [...modelCounts.entries()]
          .map(([label, value]) => ({ label, value }))
          .sort((a, b) => b.value - a.value)
          .slice(0, 12),
        "#f97316",
        value => String(Math.round(value))
      );

      const rows = document.getElementById("listing-rows");
      rows.replaceChildren();
      const sorted = [...filtered].sort((a, b) => Number(b.Price) - Number(a.Price));
      for (const item of sorted.slice(0, 500)) {
        const row = document.createElement("tr");
        for (const value of [item.Produkt, item.Model, euro.format(Number(item.Price))]) {
          const cell = document.createElement("td");
          cell.textContent = value;
          if (value.startsWith("€")) cell.className = "price";
          row.appendChild(cell);
        }
        rows.appendChild(row);
      }
      const shown = Math.min(sorted.length, 500);
      document.getElementById("table-status").textContent =
        `Showing ${shown.toLocaleString()} of ${sorted.length.toLocaleString()} matching listings`;
    }

    function downloadFilteredCsv() {
      const rows = [["Produkt", "Model", "Price"]];
      for (const item of getFilteredListings()) {
        rows.push([item.Produkt, item.Model, item.Price]);
      }
      const csv = "\uFEFF" + rows.map(row =>
        row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(",")
      ).join("\r\n");
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "iphone_listings_filtered.csv";
      link.click();
      URL.revokeObjectURL(url);
    }

    const models = [...new Set(listings.map(item => item.Model))].sort();
    for (const model of models) {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      modelFilter.appendChild(option);
    }
    const prices = listings.map(item => Number(item.Price)).filter(Number.isFinite);
    minInput.value = Math.floor(Math.min(...prices));
    maxInput.value = Math.ceil(Math.max(...prices));
    modelFilter.addEventListener("change", updateDashboard);
    minInput.addEventListener("input", updateDashboard);
    maxInput.addEventListener("input", updateDashboard);
    document.getElementById("download-button").addEventListener("click", downloadFilteredCsv);
    updateDashboard();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an interactive iPhone listings dashboard")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input listings CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output HTML dashboard")
    parser.add_argument("--no-open", action="store_true", help="Do not open the dashboard in a browser")
    args = parser.parse_args()

    try:
        data = load_data(args.input)
    except (OSError, pd.errors.ParserError, UnicodeError, ValueError) as error:
        parser.error(f"Could not load {args.input}: {error}")
    if data.empty:
        parser.error(f"No valid numeric prices found in {args.input}")

    create_dashboard(data, args.output)
    print(f"Dashboard created: {args.output.resolve()}")
    if not args.no_open:
        webbrowser.open(args.output.resolve().as_uri())


if __name__ == "__main__":
    main()
