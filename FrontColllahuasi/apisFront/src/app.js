const express = require("express");
const morgan = require("morgan");
const fs = require("fs");
const https = require("https");
const http = require("http");
// const zmq = require("zeromq/v5-compat");
// const WebSocket = require("ws");
// const wss = new WebSocket.Server({ port: 2385 });

const bodyParser = require("body-parser");
// const rateLimit = require('express-rate-limit');

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
const error = require("./red/error");
const mysql = require("./DB/mysql");
const precharge = require("./DB/prechargeMySQL");
const transporter = require("./mail");
const sendMail = require(".//modulos/mail/rutas");
const monitoreo = require("./modulos/monitoreo/rutas");
const estadisticas = require("./modulos/estadisticas/rutas");
const proxypages = require("./modulos/proxypages/rutas");
const configuration = require("./modulos/configuration/rutas");

const app = express();
// const limiter       = rateLimit({
//   windowMs: 15 * 60 * 1000,
//   max: 100,
//   standardHeaders: true,
//   legacyHeaders: false,
// });

app.use(bodyParser.json({ limit: "500kb" }));

const privateKey = fs.readFileSync("/etc/apache2/ssl/server.key", "utf8");
const certificate = fs.readFileSync("/etc/apache2/ssl/server.crt", "utf8");

const credentials = {
  key: privateKey,
  cert: certificate,
};

//Middleware
app.use((req, res, next) => {
  const allowedOrigins = [
    "http://192.168.2.223",
    "https://192.168.2.223",
    "http://192.168.2.194:8080",
    "http://192.168.2.167:8080",
    "http://192.168.1.104:8080", //Hogar
    "http://192.168.2.185:8020",
    "http://192.168.2.194:8020",
    "http://192.168.0.101:8020",
    "http://192.168.2.185",
    "https://192.168.2.152",
    "https://smartlink.hcgpe.com",
  ];
  const origin = req.headers.origin;

  // if (allowedOrigins.includes(origin)) {
  //   res.setHeader("Access-Control-Allow-Origin", origin);
  // }
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

// app.use(limiter);
app.use(morgan("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

//configuracion
app.set("port", 4159);

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

setInterval(() => {
  precharge.getClientStatusData();
  precharge.getAllTopologyData();
  precharge.getAllOperabilityLastDay();
  precharge.getAllOperability();
  precharge.preChargeDataKPI("latency");
  precharge.preChargeDataKPI("quality_lap");
  precharge.preChargeDataKPI("quality_snr");
  precharge.preChargeDataKPI("operability");
  precharge.preChargeDataKPI("temp_inst");
}, 60000);

setInterval(() => {
  precharge.getAllLatLngPMPSM();
  precharge.getAllLatLngRAJANT();
  precharge.getAllWirelessData();
  precharge.getAllWiredData();
  precharge.getCostWirelesspeers();
  precharge.getCostWiredpeers();
}, 60000);

const httpsServer = https.createServer(credentials, app);

// Crear Servidor HTTP que redirige a HTTPS
const httpServer = http.createServer((req, res) => {
  res.writeHead(301, { Location: `https://${req.headers.host}${req.url}` });
  res.end();
});

// Escuchar en puertos HTTP y HTTPS
const HTTP_PORT = 8970;
const HTTPS_PORT = 4150;

httpServer.listen(HTTP_PORT, () => {
  console.log(`Servidor HTTP redirigiendo a HTTPS en el puerto ${HTTP_PORT}`);
});

httpsServer.listen(HTTPS_PORT, () => {
  console.log(`Servidor HTTPS corriendo en el puerto ${HTTPS_PORT}`);
});

module.exports = app;
