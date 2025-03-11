const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getWorstOperability",  getWorstOperability);
router.get("/getWorstQualityLAP",   getWorstQualityLAP);
router.get("/getWorstQualitySNR",   getWorstQualitySNR);
router.get("/getWorstLatLng",       getWorstLatLng);
router.get("/getWorstLatency",      getWorstLatency);
router.get("/getTENWorstLatency",   getTENWorstLatency);
router.get("/getAlarmData",         getAlarmData);
router.get("/getDataHistory",       getDataHistory);
router.get("/getTopFiveLatency",    getTopFiveLatency);
router.get("/getWorstLatencyByIp",  getWorstLatencyByIp);
router.get("/getWorstLatLngByIp",   getWorstLatLngByIp);


async function getWorstOperability(req, res, next) {
  let macType = req.query.macType;
  try {
    await controlador.getWorstOperability(res,req.query.dateini,req.query.datefin,macType);
  } catch (error) {
    next(error);
  }
}

async function getWorstQualityLAP(req, res, next) {
  let macType = req.query.macType;
  try {
    await controlador.getWorstQualityLAP(res,req.query.dateini,req.query.datefin,macType);
  } catch (error) {
    next(error);
  }
}

async function getWorstQualitySNR(req, res, next) {
  let macType = req.query.macType;
  try {
    await controlador.getWorstQualitySNR(res,req.query.dateini,req.query.datefin,macType);
  } catch (error) {
    next(error);
  }
}

async function getTENWorstLatency(req, res, next) {
  let macType = req.query.macType;
  try {
    await controlador.getTENWorstLatency(res,req.query.dateini,req.query.datefin,macType);
  } catch (error) {
    next(error);
  }
}

async function getWorstLatLng(req, res, next) {
  try {
    await controlador.getWorstLatLng(res,req.query.dateini,req.query.datefin);
  } catch (error) {
    next(error);
  }
}

async function getWorstLatency(req, res, next) {
  let macType = req.query.macType;
  try {
    await controlador.getWorstLatency(res,req.query.dateini,req.query.datefin);
  } catch (error) {
    next(error);
  }
}

async function getAlarmData(req, res, next) {
  try {
    await controlador.getAlarmData(res,req.query.ip,req.query.dateini,req.query.datefin,req.query.alarm);
  } catch (error) {
    next(error);
  }
}

async function getDataHistory(req, res, next) {
  try {
    await controlador.getDataHistory(res);
  } catch (error) {
    next(error);
  }
}

async function getTopFiveLatency(req, res, next) {
  let macType = req.query.macType;
  try {
    await controlador.getTopFiveLatency(res,req.query.dateini,req.query.datefin, req.query.tipo,macType);
  } catch (error) {
    next(error);
  }
}

async function getWorstLatLngByIp(req, res, next) {
  try {
    await controlador.getWorstLatLngByIp(res,req.query.dateini,req.query.datefin,req.query.ip, req.query.tipo);
  } catch (error) {
    next(error);
  }
}

async function getWorstLatencyByIp(req, res, next) {
  try {
    await controlador.getWorstLatencyByIp(res,req.query.dateini,req.query.datefin,req.query.ip, req.query.tipo);
  } catch (error) {
    next(error);
  }
}


module.exports = router;
