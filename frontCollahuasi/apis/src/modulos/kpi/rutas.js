const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getAllDataKPI", getAllDataKPI);
router.get("/getCostWiredpeers", getCostWiredpeers);
router.get("/getCostWirelesspeers", getCostWirelesspeers);
router.get("/getAllLatency", getAllLatency);
router.get("/getLastConectionHaultruck", getLastConectionHaultruck);
router.get("/getCountLastConectionHaultruck", getCountLastConectionHaultruck);

//get All data from Inventory Table

//Call in DASHBOARDVIEW
//Call in KPIVIEW 
async function getAllDataKPI(req, res, next) {
  try {
    await controlador.getAllDataKPI(req.query.kpi, res);
  } catch (error) {
    next(error);
  }
}

//Call in KPIVIEW 
async function getCostWiredpeers(req, res, next) {
  try {
    await controlador.getCostWiredpeers(res);
  } catch (error) {
    next(error);
  }
}

//Call in KPIVIEW 
async function getCostWirelesspeers(req, res, next) {
  try {
    await controlador.getCostWirelesspeers(res);
  } catch (error) {
    next(error);
  }
}

//Call in ALLLATENCYVIEW
async function getAllLatency(req, res, next) {
  try {
    await controlador.getAllLatency(res);
  } catch (error) {
    next(error);
  }
}

async function getLastConectionHaultruck(req, res, next) {
  try {
    await controlador.getLastConectionHaultruck(res);
  } catch (error) {
    next(error);
  }
}

async function getCountLastConectionHaultruck(req, res, next) {
  try {
    await controlador.getCountLastConectionHaultruck(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
