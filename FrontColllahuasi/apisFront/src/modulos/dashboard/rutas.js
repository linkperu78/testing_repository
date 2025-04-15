const express = require("express");

const controlador = require("./controlador");

const router = express.Router();

router.get("/getAlarmToDashBoard", getAlarmToDashBoard);
router.get("/getAlarmRecurrentToDashBoard", getAlarmRecurrentToDashBoard);
router.get("/getKPIDashboard", getKPIDashboard);
router.get("/getAllOperability", getAllOperability);

async function getAlarmToDashBoard(req, res, next) {
  try {
    await controlador.getAlarmToDashBoard(res);
  } catch (error) {
    next(error);
  }
}

async function getAlarmRecurrentToDashBoard(req, res, next) {
  try {
    await controlador.getAlarmRecurrentToDashBoard(res);
  } catch (error) {
    next(error);
  }
}

async function getAllOperability(req, res, next) {
  try {
    await controlador.getAllOperability(res);
  } catch (error) {
    next(error);
  }
}

async function getKPIDashboard(req, res, next) {
  try {
    await controlador.getKPIDashboard(req.query.kpi, res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
