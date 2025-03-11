const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getIPLTE", getIPLTE);
router.get("/getAllLTEData", getAllLTEData);
router.get("/getAllLTEDataGraph", getAllLTEDataGraph);
router.get("/getLTE1Data", getLTE1Data);
router.get("/getSNMPModemALLDataByIP", getSNMPModemALLDataByIP);
// router.get("/lte", LTEData);

//get All data from LTE Table
// async function LTEData(req, res, next) {
//   try {
//     await controlador.getLTEData(res);
//   } catch (error) {
//     next(error);
//   }
// }

async function getIPLTE(req, res, next) {
  try {
    await controlador.getIPLTE(res);
  } catch (error) {
    next(error);
  }
}

async function getAllLTEData(req, res, next) {
  try {
    await controlador.getAllLTEData(res,req.query.ip);
  } catch (error) {
    next(error);
  }
}

async function getSNMPModemALLDataByIP(req, res, next) {
  try {
    await controlador.getSNMPModemALLDataByIP(res,req.query.ip);
  } catch (error) {
    next(error);
  }
}

async function getLTE1Data(req, res, next) {
  try {
    await controlador.getLTE1Data(res,req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in LTEGRAPHS
async function getAllLTEDataGraph(req, res, next) {
  try {
    await controlador.getAllLTEDataGraph(res,req.query.ip);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
