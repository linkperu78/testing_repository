const express = require("express");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getLastLTE", getLastLTE);
router.get("/getLast30DaysLTE", getLast30DaysLTE);
router.get("/getMaxDatesLTE", getMaxDatesLTE);

async function getLastLTE(req, res, next) {
  try {
    await controlador.getLastLTE(res, req.query.dates);
  } catch (error) {
    next(error);
  }
}

async function getLast30DaysLTE(req, res, next) {
  try {
    await controlador.getLast30DaysLTE(res);
  } catch (error) {
    next(error);
  }
}

async function getMaxDatesLTE(req, res, next) {
  try {
    await controlador.getMaxDatesLTE(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
