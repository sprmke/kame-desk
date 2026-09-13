import { useState } from "react";

export type PatientFieldState = {
  id: string;
  name: string;
  query: string;
  onQueryChange: (query: string) => void;
  onSelect: (id: string, name: string) => void;
  reset: () => void;
};

/** Search-and-select state for the patient field shared by payer workflow forms. */
export function usePatientField(): PatientFieldState {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [query, setQuery] = useState("");

  return {
    id,
    name,
    query,
    onQueryChange: (next) => {
      setQuery(next);
      setId("");
      setName("");
    },
    onSelect: (selectedId, selectedName) => {
      setId(selectedId);
      setName(selectedName);
      setQuery(selectedName);
    },
    reset: () => {
      setId("");
      setName("");
      setQuery("");
    },
  };
}
