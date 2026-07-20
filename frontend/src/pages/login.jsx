import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/login.css";

function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleLogin = (e) => {
    e.preventDefault();

    const { email, password } = formData;

    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    // TODO: replace with real auth call
    if (email === "admin@drivevitals.com" && password === "admin123") {
      navigate("/dashboard");
    } else {
      setError("Invalid email or password.");
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>DriveVitals</h1>
        <p>Sign in to your account</p>

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
            />
          </div>

          <div className="input-group">
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          {error && <p style={{ color: "#ff6b6b", marginBottom: "12px" }}>{error}</p>}

          <button type="submit" className="login-btn">Login</button>
        </form>

        <div className="forgot-password">
          <a href="#">Forgot Password?</a>
        </div>

        <div className="signup-text">
          Don't have an account? <Link to="/signup">Sign Up</Link>
        </div>
      </div>
    </div>
  );
}

export default Login;
