"use client";

import { useState, useRef } from "react";
import "../styles/dashboard.css";

export default function Home() {

  const [files,setFiles] = useState([]);
  const [token,setToken] = useState("");
  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const [view,setView] = useState("cloud");
  const [layout,setLayout] = useState("list");
  const [search,setSearch] = useState("");
  const [storage,setStorage] = useState({used:0,limit:1});

  const fileInput = useRef(null);

  /* LOGIN */

  const login = async () => {

    const res = await fetch("http://localhost:8000/login",{
      method:"POST",
      headers:{
        "Content-Type":"application/x-www-form-urlencoded"
      },
      body:new URLSearchParams({
        username:email,
        password:password
      })
    });

    const data = await res.json();

    setToken(data.access_token);

    loadFiles(data.access_token);
    loadStorage(data.access_token);
  };


  /* LOAD FILES */

  const loadFiles = async (tk = token) => {

    const res = await fetch("http://localhost:8000/my-files",{
      headers:{
        Authorization:`Bearer ${tk}`
      }
    });

    const data = await res.json();

    setFiles(data.files || []);
    setView("cloud");
  };


  /* STORAGE */

  const loadStorage = async (tk = token) => {

    const res = await fetch("http://localhost:8000/storage",{
      headers:{
        Authorization:`Bearer ${tk}`
      }
    });

    const data = await res.json();

    setStorage(data);
  };


  /* SEARCH */

  const searchFiles = async (q) => {

    setSearch(q);

    if(!q){
      loadFiles();
      return;
    }

    const res = await fetch(
      `http://localhost:8000/search?q=${q}`,
      {
        headers:{
          Authorization:`Bearer ${token}`
        }
      }
    );

    const data = await res.json();

    setFiles(data.files || []);
  };


  /* RECENT */

  const loadRecent = async () => {

    const res = await fetch("http://localhost:8000/recent",{
      headers:{
        Authorization:`Bearer ${token}`
      }
    });

    const data = await res.json();

    setFiles(data.files || []);
    setView("recent");
  };


  /* TRASH */

  const loadTrash = async () => {

    const res = await fetch("http://localhost:8000/trash",{
      headers:{
        Authorization:`Bearer ${token}`
      }
    });

    const data = await res.json();

    setFiles(data.files || []);
    setView("trash");
  };


  /* UPLOAD */

  const uploadFile = async (file) => {

    const formData = new FormData();
    formData.append("file",file);

    await fetch("http://localhost:8000/upload/",{
      method:"POST",
      headers:{
        Authorization:`Bearer ${token}`
      },
      body:formData
    });

    loadFiles();
    loadStorage();
  };


  /* DOWNLOAD */

  const downloadFile = async (filename) => {

    const res = await fetch(
      `http://localhost:8000/download/${filename}`,
      {
        headers:{
          Authorization:`Bearer ${token}`
        }
      }
    );

    const blob = await res.blob();

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;
    a.download = filename;

    document.body.appendChild(a);
    a.click();
    a.remove();
  };


  /* DELETE */

  const deleteFile = async (filename) => {

    await fetch(
      `http://localhost:8000/delete/${filename}`,
      {
        method:"DELETE",
        headers:{
          Authorization:`Bearer ${token}`
        }
      }
    );

    loadFiles();
    loadStorage();
  };


  /* RESTORE */

  const restoreFile = async (filename) => {

    await fetch(
      `http://localhost:8000/restore/${filename}`,
      {
        method:"POST",
        headers:{
          Authorization:`Bearer ${token}`
        }
      }
    );

    loadTrash();
  };


  /* SHARE */

  const shareFile = async (filename) => {

    const res = await fetch(`http://localhost:8000/share/${filename}`);

    const data = await res.json();

    navigator.clipboard.writeText(data.share_link);

    alert("Share link copied!");
  };


  /* PREVIEW */

  const previewFile = (filename) => {

    window.open(
      `http://localhost:8000/preview/${filename}`,
      "_blank"
    );
  };


  /* FILE SIZE */

  const formatSize = (bytes) => {

    return (bytes / 1000000).toFixed(2) + " MB";
  };


  /* FILE ICON */

  const getIcon = (name) => {

    if(name.endsWith(".pdf")) return "📕";
    if(name.endsWith(".png") || name.endsWith(".jpg")) return "🖼";
    if(name.endsWith(".zip")) return "🗜";
    if(name.endsWith(".mp4")) return "🎥";

    return "📄";
  };


  /* DRAG DROP */

  const handleDrop = (e) => {

    e.preventDefault();

    const file = e.dataTransfer.files[0];

    if(file){
      uploadFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };


  /* LOGIN PAGE */

  if(!token){

    return(

      <div className="login-container">

        <h1>Cloud Drive 🚀</h1>

        <input
        className="login-input"
        placeholder="Email"
        value={email}
        onChange={(e)=>setEmail(e.target.value)}
        />

        <input
        type="password"
        className="login-input"
        placeholder="Password"
        value={password}
        onChange={(e)=>setPassword(e.target.value)}
        />

        <button className="login-btn" onClick={login}>
          Login
        </button>

      </div>

    )
  }


  const percent = (storage.used/storage.limit)*100;


  return (

    <div className="container">

      {/* SIDEBAR */}

      <div className="sidebar">

        <button
        className="upload-btn"
        onClick={()=>fileInput.current.click()}
        >
          UPLOAD NEW +
        </button>

        <input
        type="file"
        hidden
        ref={fileInput}
        onChange={(e)=>uploadFile(e.target.files[0])}
        />

        <div className="menu">

          <div className="menu-item" onClick={loadFiles}>
            ☁ My Cloud
          </div>

          <div className="menu-item" onClick={loadRecent}>
            🕒 Recent
          </div>

          <div className="menu-item" onClick={loadTrash}>
            🗑 Trash
          </div>

        </div>


        {/* STORAGE BAR */}

        <div style={{marginTop:"40px"}}>

          <div>Storage</div>

          <div style={{
            background:"#ddd",
            height:"10px",
            borderRadius:"10px",
            marginTop:"8px"
          }}>

          <div style={{
            width:`${percent}%`,
            height:"10px",
            background:"#4caf50",
            borderRadius:"10px"
          }}/>

          </div>

          <small>
            {(storage.used/1000000).toFixed(2)} MB used
          </small>

        </div>

      </div>


      {/* MAIN */}

      <div className="content">

        <h2>Files</h2>

        {/* SEARCH */}

        <input
        placeholder="Search files..."
        value={search}
        onChange={(e)=>searchFiles(e.target.value)}
        style={{
          padding:"8px",
          marginBottom:"15px",
          width:"250px"
        }}
        />


        {/* VIEW TOGGLE */}

        <button onClick={()=>setLayout("list")}>List</button>
        <button onClick={()=>setLayout("grid")}>Grid</button>


        {/* DROP ZONE */}

        <div
        className="dropzone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        >
          📂 Drag & Drop Files Here
        </div>


        {/* LIST VIEW */}

        {layout==="list" && (

        <table className="files-table">

          <thead>
            <tr>
              <th>Name</th>
              <th>Size</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>

          {files.map((file)=>(

            <tr key={file.id}>

              <td onClick={()=>previewFile(file.filename)}>
                {getIcon(file.filename)} {file.filename}
              </td>

              <td>{formatSize(file.size)}</td>

              <td>

                <span onClick={()=>downloadFile(file.filename)}>⬇</span>

                <span onClick={()=>shareFile(file.filename)}>🔗</span>

                {view !== "trash" && (
                <span onClick={()=>deleteFile(file.filename)}>🗑</span>
                )}

                {view === "trash" && (
                <span onClick={()=>restoreFile(file.filename)}>♻</span>
                )}

              </td>

            </tr>

          ))}

          </tbody>

        </table>
        )}


        {/* GRID VIEW */}

        {layout==="grid" && (

        <div style={{
          display:"grid",
          gridTemplateColumns:"repeat(auto-fill,150px)",
          gap:"20px"
        }}>

        {files.map(file=>(

          <div
          key={file.id}
          style={{
            border:"1px solid #ddd",
            padding:"15px",
            textAlign:"center",
            borderRadius:"10px"
          }}
          >

            <div
            style={{fontSize:"40px"}}
            onClick={()=>previewFile(file.filename)}
            >
              {getIcon(file.filename)}
            </div>

            <div>{file.filename}</div>

            <small>{formatSize(file.size)}</small>

          </div>

        ))}

        </div>

        )}

      </div>

    </div>

  );

}