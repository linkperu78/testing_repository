const db = require("../../DB/mysql");

function getAlarmToDashBoard(res) {
  return db.getAlarmToDashBoard(res);
}

function getAlarmRecurrentToDashBoard(res) {
  return db.getAlarmRecurrentToDashBoard(res);
}

function getKPIDashboard(kpi, res) {
  return db.getKPIDashboard(kpi, res);
}

function getAllOperability(kpi, res) {
  return db.getAllOperability(kpi, res);
}

module.exports = {
  getAlarmToDashBoard,
  getKPIDashboard,
  getAllOperability,
  getAlarmRecurrentToDashBoard
};
