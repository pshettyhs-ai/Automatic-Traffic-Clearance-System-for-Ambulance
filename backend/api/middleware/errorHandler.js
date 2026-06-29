// errorHandler.js — centralised error handling so route handlers can just
// `next(err)` instead of each one inventing its own error response shape.

function notFoundHandler(req, res) {
  res.status(404).json({ error: `No route for ${req.method} ${req.originalUrl}` });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  if (status >= 500) {
    console.error("[errorHandler]", err);
  }
  res.status(status).json({
    error: err.expose ? err.message : "Internal server error",
  });
}

module.exports = { notFoundHandler, errorHandler };
