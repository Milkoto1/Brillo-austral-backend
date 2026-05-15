import React, { useState, useEffect } from 'react';

const optimizarImagen = (archivoBase64) => {
  return new Promise((resolve) => {
    const img = new Image();
    img.src = archivoBase64;
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const MAX_WIDTH = 800; 
      let width = img.width;
      let height = img.height;

      if (width > MAX_WIDTH) {
        height *= MAX_WIDTH / width;
        width = MAX_WIDTH;
      }

      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      // Usamos calidad 0.6 para asegurar que Resend no rechace el tamaño del JSON
      const resultado = canvas.toDataURL('image/jpeg', 0.6);
      resolve(resultado);
    };
  });
};

function App() {
  const [usuarioLogueado, setUsuarioLogueado] = useState('');
  const [nombreTmp, setNombreTmp] = useState('');
  const [nombre, setNombre] = useState('');
  const [direccion, setDireccion] = useState('');
  const [email, setEmail] = useState('');
  const [telefono, setTelefono] = useState('');
  const [items, setItems] = useState([{ 
    id: Date.now(), 
    tipo: 'Ventana', 
    nombrePersonalizado: '', 
    ancho: '', 
    alto: '', 
    doble_cara: false, 
    comentario: '', 
    foto: null 
  }]);
  const [totalGeneral, setTotalGeneral] = useState('0');
  const [enviando, setEnviando] = useState(false);

  const actualizarItem = (id, campo, valor) => {
    setItems(items.map(item => item.id === id ? { ...item, [campo]: valor } : item));
  };

  const manejarFoto = (id, archivo) => {
    if (!archivo) return;
    const reader = new FileReader();
    reader.onloadend = async () => {
      const fotoOptimizada = await optimizarImagen(reader.result);
      actualizarItem(id, 'foto', fotoOptimizada);
    };
    reader.readAsDataURL(archivo);
  };

  useEffect(() => {
    let suma = 0;
    items.forEach(i => {
      const a = parseFloat(String(i.ancho).replace(',', '.')) || 0;
      const h = parseFloat(String(i.alto).replace(',', '.')) || 0;
      suma += (a * h * (i.doble_cara ? 2 : 1));
    });
    setTotalGeneral(suma.toFixed(2).replace('.', ','));
  }, [items]);

  const enviarReporte = async () => {
    if (!nombre || !direccion || !email) return alert("Faltan campos obligatorios (*)");
    setEnviando(true);
    const payload = {
      cliente_nombre: nombre, direccion, email_cliente: email,
      usuario_emisor: usuarioLogueado, telefono,
      items: items.map(i => ({
        nombre_item: i.tipo === 'Otro' ? i.nombrePersonalizado : i.tipo,
        ancho: parseFloat(String(i.ancho).replace(',', '.')) || 0,
        alto: parseFloat(String(i.alto).replace(',', '.')) || 0,
        doble_cara: i.doble_cara,
        comentario: i.comentario,
        foto_base64: i.foto
      }))
    };
    try {
      const res = await fetch('https://brillo-austral-backend.onrender.com/reporte', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        alert("¡Reporte enviado exitosamente!");
        setItems([{ id: Date.now(), tipo: 'Ventana', nombrePersonalizado: '', ancho: '', alto: '', doble_cara: false, comentario: '', foto: null }]);
        setNombre(''); setDireccion(''); setEmail(''); setTelefono('');
      } else { alert("Error en el servidor"); }
    } catch { alert("Error de conexión"); }
    finally { setEnviando(false); }
  };

  const inputS = { width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #ccc', marginBottom: '10px', boxSizing: 'border-box' };

  if (!usuarioLogueado) {
    return (
      <div style={{ padding: '50px 20px', textAlign: 'center', fontFamily: 'Arial' }}>
        <h2 style={{ color: '#005f8d' }}>Brillo Austral PV</h2>
        <input type="text" placeholder="Tu nombre" value={nombreTmp} onChange={e => setNombreTmp(e.target.value)} style={inputS} />
        <button onClick={() => setUsuarioLogueado(nombreTmp)} style={{ width: '100%', padding: '15px', borderRadius: '30px', border: 'none', backgroundColor: '#005f8d', color: 'white', fontWeight: 'bold' }}>Entrar</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '15px', fontFamily: 'Arial', backgroundColor: '#f0f4f8', minHeight: '100vh' }}>
      <div style={{ backgroundColor: 'white', padding: '15px', borderRadius: '15px', marginBottom: '20px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
        <p>👤 Trabajador: <b>{usuarioLogueado}</b></p>
        <input placeholder="Cliente *" value={nombre} onChange={e => setNombre(e.target.value)} style={inputS} />
        <input placeholder="Dirección *" value={direccion} onChange={e => setDireccion(e.target.value)} style={inputS} />
        <input placeholder="Email *" value={email} onChange={e => setEmail(e.target.value)} style={inputS} />
        <input placeholder="Teléfono" value={telefono} onChange={e => setTelefono(e.target.value)} style={inputS} />
      </div>

      {items.map((item, index) => (
        <div key={item.id} style={{ backgroundColor: 'white', padding: '15px', borderRadius: '15px', marginBottom: '15px', borderLeft: '5px solid #005f8d', position: 'relative' }}>
          <button onClick={() => items.length > 1 && setItems(items.filter(i => i.id !== item.id))} style={{ position: 'absolute', right: '10px', top: '10px', border: 'none', background: 'none', color: 'red' }}>✕</button>
          <p style={{ fontWeight: 'bold', color: '#005f8d' }}>ÍTEM #{index + 1}</p>
          
          <select value={item.tipo} onChange={e => actualizarItem(item.id, 'tipo', e.target.value)} style={inputS}>
            <option value="Ventana">Ventana</option>
            <option value="Panel">Panel</option>
            <option value="Puerta">Puerta</option>
            <option value="Otro">Otro (Especificar)</option>
          </select>

          {item.tipo === 'Otro' && (
            <input placeholder="¿Qué es? (Ej: Espejo)" value={item.nombrePersonalizado} onChange={e => actualizarItem(item.id, 'nombrePersonalizado', e.target.value)} style={inputS} />
          )}

          <div style={{ display: 'flex', gap: '10px' }}>
            <input placeholder="Ancho" value={item.ancho} onChange={e => actualizarItem(item.id, 'ancho', e.target.value)} style={inputS} />
            <input placeholder="Alto" value={item.alto} onChange={e => actualizarItem(item.id, 'alto', e.target.value)} style={inputS} />
          </div>

          <label style={{ display: 'block', marginBottom: '10px', fontSize: '14px' }}>
            <input type="checkbox" checked={item.doble_cara} onChange={e => actualizarItem(item.id, 'doble_cara', e.target.checked)} /> Limpieza Doble Cara (x2)
          </label>

          <input placeholder="Comentario opcional..." value={item.comentario} onChange={e => actualizarItem(item.id, 'comentario', e.target.value)} style={{ ...inputS, fontSize: '12px' }} />

          <label style={{ display: 'block', backgroundColor: item.foto ? '#c6f6d5' : '#e2e8f0', padding: '10px', borderRadius: '8px', textAlign: 'center', cursor: 'pointer' }}>
            {item.foto ? '✅ Foto Lista' : '📷 Abrir Cámara'}
            <input type="file" accept="image/*" capture="environment" onChange={e => manejarFoto(item.id, e.target.files[0])} style={{ display: 'none' }} />
          </label>
        </div>
      ))}

      <button onClick={() => setItems([...items, { id: Date.now(), tipo: 'Ventana', nombrePersonalizado: '', ancho: '', alto: '', doble_cara: false, comentario: '', foto: null }])} style={{ width: '100%', padding: '12px', marginBottom: '20px', borderRadius: '10px', border: '1px dashed #005f8d', color: '#005f8d', background: 'none', fontWeight: 'bold' }}>+ Agregar Item</button>
      
      <div style={{ backgroundColor: '#0f172a', color: 'white', padding: '20px', borderRadius: '15px', textAlign: 'center' }}>
        <h2 style={{ margin: 0 }}>TOTAL: {totalGeneral} m²</h2>
      </div>

      <button onClick={enviarReporte} disabled={enviando} style={{ width: '100%', padding: '20px', borderRadius: '35px', border: 'none', backgroundColor: enviando ? '#ccc' : '#005f8d', color: 'white', fontWeight: 'bold', marginTop: '15px' }}>
        {enviando ? 'Enviando...' : 'ENVIAR REPORTE'}
      </button>
    </div>
  );
}

export default App;
