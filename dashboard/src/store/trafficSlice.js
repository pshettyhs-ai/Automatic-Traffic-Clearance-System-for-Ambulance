import { createSlice } from "@reduxjs/toolkit";

const LANES = [1, 2, 3, 4];

const initialState = {
  socketStatus: "disconnected", // disconnected | connecting | connected
  lanes: LANES.reduce((acc, lane) => {
    acc[lane] = { lane, phase: "UNKNOWN", updatedAt: null };
    return acc;
  }, {}),
  emergencyActive: false,
  activeEmergencyLane: null,
  emergencyEvents: [], // newest first, capped client-side
  systemHealth: {}, // node -> latest heartbeat
};

const MAX_EVENTS_IN_MEMORY = 200;

const trafficSlice = createSlice({
  name: "traffic",
  initialState,
  reducers: {
    setSocketStatus(state, action) {
      state.socketStatus = action.payload;
    },
    hydrateEvents(state, action) {
      state.emergencyEvents = action.payload.slice(0, MAX_EVENTS_IN_MEMORY);
    },
    laneStatusReceived(state, action) {
      const { lane, phase } = action.payload;
      if (!state.lanes[lane]) {
        state.lanes[lane] = { lane, phase: "UNKNOWN", updatedAt: null };
      }
      state.lanes[lane].phase = phase;
      state.lanes[lane].updatedAt = Date.now();
    },
    emergencyEventReceived(state, action) {
      state.emergencyActive = true;
      state.activeEmergencyLane = action.payload.lane;
      state.emergencyEvents.unshift(action.payload);
      state.emergencyEvents = state.emergencyEvents.slice(0, MAX_EVENTS_IN_MEMORY);
    },
    emergencyCleared(state) {
      state.emergencyActive = false;
      state.activeEmergencyLane = null;
    },
    systemHealthReceived(state, action) {
      const { node } = action.payload;
      state.systemHealth[node] = { ...action.payload, receivedAt: Date.now() };
    },
  },
});

export const {
  setSocketStatus,
  hydrateEvents,
  laneStatusReceived,
  emergencyEventReceived,
  emergencyCleared,
  systemHealthReceived,
} = trafficSlice.actions;

export default trafficSlice.reducer;
