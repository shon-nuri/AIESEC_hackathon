import React, { useState } from 'react';

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const API_BASE = 'http://localhost:8000';

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
      if (!allowedTypes.includes(selectedFile.type) && !selectedFile.name.toLowerCase().endsWith('.pdf')) {
        setError('Please select a valid file (JPEG, PNG, PDF)');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setResult(null);
      setError('');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
      if (!allowedTypes.includes(droppedFile.type) && !droppedFile.name.toLowerCase().endsWith('.pdf')) {
        setError('Please select a valid file (JPEG, PNG, PDF)');
        return;
      }
      setFile(droppedFile);
      setResult(null);
      setError('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const detectAll = async () => {
    if (!file) return;
    
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_BASE}/api/detect/all`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Detection failed');
      }
    } catch (err) {
      setError('Connection error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setResult(null);
    setError('');
  };

  const downloadJSON = () => {
    if (!result) return;
    
    const json = JSON.stringify(result, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'detection_results.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif',
      background: '#f5f5f5',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      margin: 0,
    }}>
      {/* Header */}
      <div style={{
        background: '#2c3e50',
        color: 'white',
        padding: '20px 40px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ fontSize: '24px', fontWeight: 600 }}>DocProcessor</div>
        <button 
          onClick={downloadJSON}
          disabled={!result}
          style={{
            background: result ? '#3498db' : '#95a5a6',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            fontSize: '14px',
            borderRadius: '6px',
            cursor: result ? 'pointer' : 'not-allowed',
            transition: 'background 0.3s',
          }}
        >
          Download in JSON format
        </button>
      </div>

      {/* Container */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '40px 20px',
        flex: 1,
        width: '100%',
      }}>
        {/* Upload Area */}
        {!file && (
          <div 
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            style={{
              background: dragOver ? '#ebf8ff' : 'white',
              border: `3px dashed ${dragOver ? '#3498db' : '#cbd5e0'}`,
              borderRadius: '12px',
              padding: '80px 40px',
              textAlign: 'center',
              transition: 'all 0.3s',
              cursor: 'pointer',
            }}
          >
            <input 
              type="file" 
              id="fileInput"
              onChange={handleFileChange} 
              accept=".jpg,.jpeg,.png,.pdf,image/*,application/pdf"
              style={{ display: 'none' }}
            />
            <button 
              onClick={() => document.getElementById('fileInput').click()}
              style={{
                background: '#3498db',
                color: 'white',
                border: 'none',
                padding: '16px 32px',
                fontSize: '16px',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background 0.3s',
              }}
            >
              Upload File
            </button>
            <div style={{ marginTop: '16px', color: '#718096', fontSize: '14px' }}>
              or drag and drop file anywhere
            </div>
          </div>
        )}

        {/* File Info */}
        {file && !result && (
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '12px',
            marginTop: '20px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '18px', marginBottom: '20px', color: '#2d3748' }}>
              {file.name}
            </div>
            <button 
              onClick={detectAll}
              disabled={loading}
              style={{
                background: loading ? '#95a5a6' : '#27ae60',
                color: 'white',
                border: 'none',
                padding: '16px 48px',
                fontSize: '16px',
                borderRadius: '8px',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.3s',
              }}
            >
              {loading ? 'Processing...' : 'Process'}
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            background: '#fee',
            color: '#c33',
            padding: '16px',
            borderRadius: '8px',
            marginTop: '20px',
            textAlign: 'center',
          }}>
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div style={{ marginTop: '40px' }}>
            {result.file_type === 'pdf' ? (
              <>
                {result.pages.map((page, index) => (
                  <div key={index} style={{
                    background: 'white',
                    borderRadius: '12px',
                    padding: '24px',
                    marginBottom: '24px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  }}>
                    <div style={{
                      fontSize: '20px',
                      fontWeight: 600,
                      color: '#2d3748',
                      marginBottom: '20px',
                      textAlign: 'center',
                    }}>
                      Page {page.page}
                    </div>
                    <div style={{
                      width: '100%',
                      maxWidth: '600px',
                      margin: '0 auto',
                      background: '#e2e8f0',
                      borderRadius: '8px',
                      overflow: 'hidden',
                    }}>
                      {page.result_image_url && (
                        <img 
                          src={`${API_BASE}${page.result_image_url}`} 
                          alt={`Page ${page.page}`}
                          style={{ width: '100%', height: 'auto', display: 'block' }}
                        />
                      )}
                    </div>
                  </div>
                ))}

                {/* Summary */}
                <div style={{
                  background: 'white',
                  borderRadius: '12px',
                  padding: '30px',
                  marginTop: '24px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  textAlign: 'center',
                }}>
                  <div style={{
                    fontSize: '22px',
                    fontWeight: 600,
                    color: '#2d3748',
                    marginBottom: '20px',
                  }}>
                    Total Found in Document
                  </div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    gap: '40px',
                    flexWrap: 'wrap',
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: 700, color: '#3498db' }}>
                        {result.total_counts?.signatures || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
                        Signatures
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: 700, color: '#3498db' }}>
                        {result.total_counts?.stamps || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
                        Seals
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: 700, color: '#3498db' }}>
                        {result.total_counts?.qr_codes || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
                        QR Codes
                      </div>
                    </div>
                  </div>
                </div>

                {/* Add Another File Button */}
                <div style={{ textAlign: 'center', marginTop: '24px' }}>
                  <button 
                    onClick={resetUpload}
                    style={{
                      background: '#27ae60',
                      color: 'white',
                      border: 'none',
                      padding: '16px 48px',
                      fontSize: '16px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'background 0.3s',
                    }}
                  >
                    Add another file
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Single Image Result */}
                <div style={{
                  background: 'white',
                  borderRadius: '12px',
                  padding: '24px',
                  marginBottom: '24px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                }}>
                  <div style={{
                    fontSize: '20px',
                    fontWeight: 600,
                    color: '#2d3748',
                    marginBottom: '20px',
                    textAlign: 'center',
                  }}>
                    Detection Result
                  </div>
                  <div style={{
                    width: '100%',
                    maxWidth: '600px',
                    margin: '0 auto',
                    background: '#e2e8f0',
                    borderRadius: '8px',
                    overflow: 'hidden',
                  }}>
                    {result.result_image_url && (
                      <img 
                        src={`${API_BASE}${result.result_image_url}`} 
                        alt="Detection result"
                        style={{ width: '100%', height: 'auto', display: 'block' }}
                      />
                    )}
                  </div>
                </div>

                {/* Summary for single image */}
                <div style={{
                  background: 'white',
                  borderRadius: '12px',
                  padding: '30px',
                  marginTop: '24px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  textAlign: 'center',
                }}>
                  <div style={{
                    fontSize: '22px',
                    fontWeight: 600,
                    color: '#2d3748',
                    marginBottom: '20px',
                  }}>
                    Total Found in Image
                  </div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    gap: '40px',
                    flexWrap: 'wrap',
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: 700, color: '#3498db' }}>
                        {result.counts?.signatures || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
                        Signatures
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: 700, color: '#3498db' }}>
                        {result.counts?.stamps || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
                        Seals
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: 700, color: '#3498db' }}>
                        {result.counts?.qr_codes || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
                        QR Codes
                      </div>
                    </div>
                  </div>
                </div>

                {/* Add Another File Button */}
                <div style={{ textAlign: 'center', marginTop: '24px' }}>
                  <button 
                    onClick={resetUpload}
                    style={{
                      background: '#27ae60',
                      color: 'white',
                      border: 'none',
                      padding: '16px 48px',
                      fontSize: '16px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'background 0.3s',
                    }}
                  >
                    Add another file
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        background: '#2c3e50',
        color: 'white',
        padding: '30px 40px',
        textAlign: 'center',
        marginTop: 'auto',
      }}>
        <div style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px' }}>
          Team S101
        </div>
        <div style={{ fontSize: '14px', color: '#bdc3c7' }}>
          Aitbayev Aslanbek, Kaltayev Ernur, Nadyrkhan Shyntemir
        </div>
      </div>
    </div>
  );
}

export default App;