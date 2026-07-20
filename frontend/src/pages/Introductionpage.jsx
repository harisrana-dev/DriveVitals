import "../styles/Introductionpage.css";
import { useNavigate } from "react-router-dom";

function GetStarted() {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate("/login"); 
  };

  return (
    <div className="fragment">
      <div className="main-content">
        <button className="get-started-btn" onClick={handleClick}>
          Get Started
        </button>
      </div>
    </div>
  );
}

export default GetStarted;