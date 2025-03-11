const db = require("../../DB/mysql");

function getPageStatus(res) {
  return db.getPageStatus(res);
}



module.exports = {
  getPageStatus,
};
