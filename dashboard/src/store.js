import { configureStore } from "@reduxjs/toolkit";
import trafficReducer from "./store/trafficSlice.js";

export const store = configureStore({
  reducer: {
    traffic: trafficReducer,
  },
});
