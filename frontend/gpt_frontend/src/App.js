// import logo from './logo.svg';
// import './App.css';
// import MapComponent from './MapComponent';
// import ShapefileComponent from './ShapefileComponent';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;

import React, { useState, useEffect } from 'react';
import './App.css';
import MapComponent from './MapComponent';
import FileSelector from './FileSelector.js';
import QueryInput from './QueryInput';

export const SelectedFileContext = React.createContext();

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  
  // add tidio chatbot
  
  useEffect(() => {
    // Load Tidio script on component mount
    const script = document.createElement('script');
    script.src = 'https://code.tidio.co/tmvcyrnqnvdk2xuajiyewmfakmvekzlw.js';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      // Clean up Tidio script on component unmount
      document.body.removeChild(script);
    };
  }, []);


  return (
    <div className="App">
      <SelectedFileContext.Provider value={ [selectedFile, setSelectedFile ]}>
        <MapComponent />
        {/* <QueryInput /> */}
        {/* <FileSelector /> */}
      </SelectedFileContext.Provider>
    </div>
  );
}

export default App;


