import { useState } from 'react';

export const useDatasets = () => {
  const [savedDatasets, setSavedDatasets] = useState([]);

  const addDataset = (newDataset) => {
    setSavedDatasets(prev => [newDataset, ...prev]);
  };

  return {
    savedDatasets,
    addDataset
  };
};