const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getIPServer", getIPServer);
router.get("/getAllServerData", getAllServerData);
router.get("/getAllServerGraphData", getAllServerGraphData);
router.get("/getVirMacServer", getVirMacServer);
router.get("/getVirMacByIP", getVirMacByIP);
router.get("/getAlarmVirMac", getAlarmVirMac);


//Call in SERVERVIEW
async function getIPServer(req, res, next) {
  try {
    await controlador.getIPServer(res);
  } catch (error) {
    next(error);
  }
}

//Call in SERVERVIEW
async function getAllServerData(req, res, next) {
  try {
    await controlador.getAllServerData(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

// async function allDataServer(req, res, next) {
//   try {
//     await controlador.allDataServer(res, req.query.ip);
//   } catch (error) {
//     next(error);
//   }
// }

//Call in LTEGRAPHS
async function getAllServerGraphData(req, res, next) {
  try {
    await controlador.getAllServerGraphData(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}


// Call in DashBoard (ip 172.16.96.102)
async function getVirMacServer(req, res, next) {
  try {
    await controlador.getVirMacServer(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

async function getVirMacByIP(req, res, next) {
  try {
    await controlador.getVirMacByIP(res, req.query.ip, req.query.vm);
  } catch (error) {
    next(error);
  }
}

async function getAlarmVirMac(req, res, next) {
  try {
    await controlador.getAlarmVirMac(res, req.query.ip, req.query.vm);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
