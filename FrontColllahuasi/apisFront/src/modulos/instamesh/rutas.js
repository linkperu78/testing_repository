const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getAllWirelessData", getAllWirelessData);
router.get("/getAllWiredData", getAllWiredData);
router.get("/getAllTempData", getAllTempData);
router.get("/getAllCostData", getAllCostData);
router.get("/getAllCostJRData", getAllCostJRData);
router.get("/getAllIPS", getAllIPS);
router.get("/getAllWirelessDataByIP", getAllWirelessDataByIP);
router.get("/getAllWiredDataByIP", getAllWiredDataByIP);
router.get("/getAllTempDataByIP", getAllTempDataByIP);
router.get("/getAllCostDataByIP", getAllCostDataByIP);
router.get("/getAllCostJRDataByIP", getAllCostJRDataByIP);

//Call in LISTKPI
async function getAllWirelessData(req, res, next) {
  try {
    await controlador.getAllWirelessData(res);
  } catch (error) {
    next(error);
  }
}

//Call in LISTKPI
async function getAllWiredData(req, res, next) {
  try {
    await controlador.getAllWiredData(res);
  } catch (error) {
    next(error);
  }
}

//Call in LISTKPI
async function getAllTempData(req, res, next) {
  try {
    await controlador.getAllTempData(res);
  } catch (error) {
    next(error);
  }
}

async function getAllIPS(req, res, next) {
  try {
    await controlador.getAllIPS(res);
  } catch (error) {
    next(error);
  }
}

//Call in LISTKPI
//Call in COSTMAPSVIEW
async function getAllCostData(req, res, next) {
  try {
    await controlador.getAllCostData(res);
  } catch (error) {
    next(error);
  }
}

//Call in LISTKPI
async function getAllCostJRData(req, res, next) {
  try {
    await controlador.getAllCostJRData(res);
  } catch (error) {
    next(error);
  }
}

//Call in INSTAMESHGRAPHS
async function getAllWirelessDataByIP(req, res, next) {
  try {
    await controlador.getAllWirelessDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in INSTAMESHGRAPHS
async function getAllWiredDataByIP(req, res, next) {
  try {
    await controlador.getAllWiredDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in INSTAMESHGRAPHS
async function getAllTempDataByIP(req, res, next) {
  try {
    await controlador.getAllTempDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in INSTAMESHGRAPHS
async function getAllCostDataByIP(req, res, next) {
  try {
    await controlador.getAllCostDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in INSTAMESHGRAPHS
async function getAllCostJRDataByIP(req, res, next) {
  try {
    await controlador.getAllCostJRDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
