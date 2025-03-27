const express = require("express");
const morgan = require("morgan");
// const fs = require("fs");
// const https = require("https");
// const http = require("http");

// PUERTOS
// const HTTP_PORT = 8970;
// const HTTPS_PORT = 4150;
const MYSQL_PORT = 4159;

const bodyParser = require("body-parser");

const inventario = require("./modulos/inventario/rutas");
const kpi = require("./modulos/kpi/rutas");
const topology = require("./modulos/topology/rutas");
const predict = require("./modulos/predict/rutas");
const LTE = require("./modulos/lte/rutas");
const server = require("./modulos/server/rutas");
const login = require("./modulos/login/rutas");
const clustering = require("./modulos/clustering/rutas");
const maps = require("./modulos/maps/rutas");
const instamesh = require("./modulos/instamesh/rutas");
const csv = require("./modulos/csvInventory/rutas");
const dbstatus = require("./modulos/databasestatus/rutas");
const statuspage = require("./modulos/change_priv/rutas");
const dashboard = require("./modulos/dashboard/rutas");
const report = require("./modulos/report/rutas");
const rutaYAML = require("./modulos/yaml/rutas");
const precharge = require("./DB/prechargeMySQL");
const sendMail = require(".//modulos/mail/rutas");
const monitoreo = require("./modulos/monitoreo/rutas");
const estadisticas = require("./modulos/estadisticas/rutas");
const proxypages = require("./modulos/proxypages/rutas");
const configuration = require("./modulos/configuration/rutas");
const error = require("./red/error");

const app = express();

app.use(bodyParser.json({ limit: "500kb" }));

//Middleware
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Credentials", "true");
  res.header(
    "Access-Control-Allow-Headers",
    "Authorization, X-API-KEY, Origin, X-Requested-With, Content-Type, Accept, Access-Control-Allow-Request-Method"
  );
  res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE");
  res.header("Allow", "GET, POST, OPTIONS, PUT, DELETE");
  res.setHeader("Transfer-Encoding", "chunked");
  next();
});

app.use(morgan("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

//configuracion
app.set("port", MYSQL_PORT);

//rutas
app.use("/api/inventario", inventario);
app.use("/api/kpi", kpi);
app.use("/api/topology", topology);
app.use("/api/predict", predict);
app.use("/api/lte", LTE);
app.use("/api/server", server);
app.use("/api/clustering", clustering);
app.use("/api/login", login);
app.use("/api/maps", maps);
app.use("/api/instamesh", instamesh);
app.use("/api/csv", csv);
app.use("/api/dbstatus", dbstatus);
app.use("/api/pagestatus", statuspage);
app.use("/api/dashboard", dashboard);
app.use("/api/report", report);
app.use("/api/rutaYAML", rutaYAML);
app.use("/api/sendMail", sendMail);
app.use("/api/GestorHCGLink/monitoreo", monitoreo);
app.use("/api/GestorHCGLink/proxypages", proxypages);
app.use("/api/GestorHCGLink/configuration", configuration);
app.use("/api/GestorHCGLink/estadisticas", estadisticas);
app.use(error);

async function getDataCharge() {
  precharge.getAllSNRData();
  precharge.getAllIPS();
  precharge.getAllLatLngPMPSM();
  precharge.getAllLatLngRAJANT();
  precharge.preChargeDataKPI("latency");
  precharge.preChargeDataKPI("quality_lap");
  precharge.preChargeDataKPI("quality_snr");
  precharge.preChargeDataKPI("pack_inst");
  precharge.preChargeDataKPI("temp_inst");
  precharge.preChargeDataKPI("wire_inst");
  precharge.preChargeDataKPI("operability");
  precharge.preChargeDataKPI("kpisnr");
  precharge.getAllOperability();
  precharge.getAllOperabilityLastDay();
  await precharge.getAllWirelessData();
  await precharge.getAllWiredData();
  await precharge.getAllTempData();
}

async function getTopologyStatus() {
  precharge.getAllTopologyData();
  precharge.getAllPredictRXLVLData();
}

async function getDBSTATUS() {
  precharge.getDataBaseStatus();
}

async function getCostsData() {
  precharge.getAllRajantDataLastMinute();
  precharge.getLastConectionHaultruck();
  precharge.getCountLastConectionHaultruck();
  precharge.getAllCostJRData();
  precharge.getAllCostData();
}

async function getKpiCostData() {
  precharge.getAllHaulTrucksDrive();
  precharge.getCostWiredpeers();
  precharge.getCostWirelesspeers();
}

function comprobarHora() {
  let currentMinute = new Date().getMinutes();

  if (
    currentMinute == 1 ||
    currentMinute == 16 ||
    currentMinute == 31 ||
    currentMinute == 46
  ) {
    getDataCharge();
  }

  if (
    currentMinute == 8 ||
    currentMinute == 23 ||
    currentMinute == 38 ||
    currentMinute == 53
  ) {
    getDBSTATUS();
    getCostsData();
    getKpiCostData();
  }

  if (
    currentMinute == 5 ||
    currentMinute == 20 ||
    currentMinute == 35 ||
    currentMinute == 50
  ) {
    getTopologyStatus();
  }
}

setInterval(() => {
  comprobarHora();
}, 60000);

setTimeout(() => {
  getDataCharge();
  getDBSTATUS();
  getCostsData();
  getKpiCostData();
  getTopologyStatus();
}, 100);

// para hacerlo HTTPS

// const privateKey = fs.readFileSync("/etc/apache2/ssl/server.key", "utf8");
// const certificate = fs.readFileSync("/etc/apache2/ssl/server.crt", "utf8");

// const credentials = {
//   key: privateKey,
//   cert: certificate,
// };

// const httpsServer = https.createServer(credentials, app);

// const httpServer = http.createServer((req, res) => {
//   res.writeHead(301, { Location: `https://${req.headers.host}${req.url}` });
//   res.end();
// });

// httpServer.listen(HTTP_PORT, () => {
//   console.log(`Servidor HTTP redirigiendo a HTTPS en el puerto ${HTTP_PORT}`);
// });

// httpsServer.listen(HTTPS_PORT, () => {
//   console.log(`Servidor HTTPS corriendo en el puerto ${HTTPS_PORT}`);
// });

module.exports = app;
