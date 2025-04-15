const db = require("../../DB/mysql");

function getLastLTE(res, dates) {
  return db.getLastLTE(res, dates);
}

function getLast30DaysLTE(res) {
  return db.getLast30DaysLTE(res);
}

function getMaxDatesLTE(res) {
  return db.getMaxDatesLTE(res);
}

module.exports = {
  getLastLTE,
  getLast30DaysLTE,
  getMaxDatesLTE,
};
