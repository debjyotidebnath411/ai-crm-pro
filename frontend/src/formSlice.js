import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  hcp_name: "",
  interaction_type: "Meeting",

  date: "",
  time: "",

  attendees: "",

  topics: "",
  materials: "",
  samples: "",

  sentiment: "Neutral",

  outcomes: "",
  follow_up: ""
};

const formSlice = createSlice({
  name: "form",
  initialState,

  reducers: {
    updateField: (state, action) => {
      const { field, value } = action.payload;
      state[field] = value;
    },

    updateForm: (state, action) => {
      Object.assign(state, action.payload);
    },

    resetForm: () => ({
      ...initialState
    })
  }
});

export const {
  updateField,
  updateForm,
  resetForm
} = formSlice.actions;

export default formSlice.reducer;
