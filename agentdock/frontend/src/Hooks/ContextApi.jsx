import React, { useState, useEffect } from "react";

const Context = React.createContext();
const AppContext = ({ children }) => {
  const [respData, setRespData] = useState();
  //------------------------------------------------------

  const _set_data = (value) => {
    return setRespData(value);
  };

  //------------------------------------------------------
  useEffect(() => {
    return () => {
      //cleanup
    };
  }, []);
  //------------------------------------------------------
  const bundle = {
    respData,
    _set_data,
  };
  return <Context.Provider value={bundle}>{children}</Context.Provider>;
};

export default AppContext;
export const useAppContext = () => React.useContext(Context);
