import { io } from "socket.io-client";
import { API_BASE_URL } from "./api.js";
import {
  setSocketStatus,
  laneStatusReceived,
  emergencyEventReceived,
  emergencyCleared,
  systemHealthReceived,
} from "../store/trafficSlice.js";

let socket = null;

/**
 * Wires the Socket.IO client straight into Redux dispatch, so components
 * never touch the socket directly — they just read from the store. Call
 * once from the top-level App component.
 */
export function initSocket(dispatch) {
  if (socket) return socket;

  dispatch(setSocketStatus("connecting"));
  socket = io(API_BASE_URL, { reconnectionDelay: 1000, reconnectionDelayMax: 5000 });

  socket.on("connect", () => dispatch(setSocketStatus("connected")));
  socket.on("disconnect", () => dispatch(setSocketStatus("disconnected")));
  socket.on("connect_error", () => dispatch(setSocketStatus("disconnected")));

  socket.on("laneStatus", (payload) => dispatch(laneStatusReceived(payload)));
  socket.on("emergencyEvent", (payload) => dispatch(emergencyEventReceived(payload)));
  socket.on("emergencyCleared", (payload) => dispatch(emergencyCleared(payload)));
  socket.on("systemHealth", (payload) => dispatch(systemHealthReceived(payload)));

  return socket;
}

export function getSocket() {
  return socket;
}
