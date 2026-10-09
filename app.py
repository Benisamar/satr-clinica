import { useState, type FormEvent } from "react";
import { useAuth } from "../context/AuthContext";
import { Alert } from "../components/ui";
import { ROLES_LABELS } from "../lib/types";
import type { Rol } from "../lib/types";

const medicalImage =
  "https://images.pexels.com/photos/4173250/pexels-photo-4173250.jpeg?auto=compress&cs=tinysrgb&h=650&w=940";

export function LoginPage() {
  const { signIn, signUp } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nombre, setNombre] = useState("");
  const [rol, setRol] = useState<Rol>("pasante");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function changeMode(nextMode: "login" | "register") {
    setMode(nextMode);
    setError(null);
    setSuccess(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!email.trim() || !password) {
      setError("Complete el correo electrónico y la contraseña.");
      return;
    }

    if (mode === "register" && !nombre.trim()) {
      setError("Ingrese su nombre completo.");
      return;
    }

    setSubmitting(true);

    if (mode === "login") {
      const { error: signInError } = await signIn(email.trim(), password);

      if (signInError) {
        setError(signInError);
      }
    } else {
      const { error: signUpError } = await signUp(
        email.trim(),
        password,
        nombre.trim(),
        rol
      );

      if (signUpError) {
        setError(signUpError);
      } else {
        setSuccess(
          "Cuenta creada correctamente. Ahora puede iniciar sesión."
        );
        setMode("login");
        setPassword("");
      }
    }

    setSubmitting(false);
  }

  return (
    <main className="min-h-screen bg-[#0d1016] text-white lg:grid lg:grid-cols-[302px_minmax(360px,460px)_1fr]">
      <aside className="flex min-h-screen flex-col justify-between bg-[#252731] px-5 py-8">
        <div>
          <div className="mb-12">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-amber-300 bg-amber-300/10 text-2xl">
                S
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-300">
                  Plataforma clínica
                </p>
                <h1 className="text-xl font-bold tracking-wide text-white">
                  S.A.T.R.
                </h1>
              </div>
            </div>

            <p className="max-w-[230px] text-sm leading-6 text-slate-300">
              Sistema de Atención, Tratamiento y Registro para equipos de salud.
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-black/10 p-4">
            <div className="mb-4 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                Acceso seguro
              </span>
            </div>

            <p className="text-sm leading-6 text-slate-400">
              Ingrese con sus credenciales para acceder a los módulos clínicos.
            </p>
          </div>
        </div>

        <div className="border-t border-white/10 pt-5 text-xs leading-5 text-slate-400">
          <p>Acceso restringido a personal autorizado.</p>
          <p className="mt-1 text-slate-500">S.A.T.R. Plataforma de salud</p>
        </div>
      </aside>

      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.18em] text-cyan-400">
              Bienvenido
            </p>

            <h2 className="text-3xl font-bold tracking-tight text-white">
              {mode === "login" ? "Iniciar sesión" : "Crear una cuenta"}
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              {mode === "login"
                ? "Acceda a su espacio de trabajo clínico."
                : "Registre sus datos para solicitar acceso al sistema."}
            </p>
          </div>

          <div className="mb-7 grid grid-cols-2 gap-2 rounded-lg border border-white/10 bg-[#171a22] p-1">
            <button
              type="button"
              onClick={() => changeMode("login")}
              className={`rounded-md px-3 py-2.5 text-sm font-semibold transition ${
                mode === "login"
                  ? "bg-cyan-400 text-[#0d1016] shadow-lg shadow-cyan-400/10"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              Iniciar sesión
            </button>

            <button
              type="button"
              onClick={() => changeMode("register")}
              className={`rounded-md px-3 py-2.5 text-sm font-semibold transition ${
                mode === "register"
                  ? "bg-cyan-400 text-[#0d1016] shadow-lg shadow-cyan-400/10"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              Registrarse
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {mode === "register" && (
              <div>
                <label
                  htmlFor="nombre"
                  className="mb-2 block text-sm font-medium text-slate-200"
                >
                  Nombre completo
                </label>

                <input
                  id="nombre"
                  type="text"
                  value={nombre}
                  onChange={(event) => setNombre(event.target.value)}
                  placeholder="Ej. Juan Pérez"
                  autoComplete="name"
                  className="w-full rounded-lg border border-white/10 bg-[#171a22] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                />
              </div>
            )}

            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-200"
              >
                Correo electrónico
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="correo@clinica.com"
                autoComplete="email"
                required
                className="w-full rounded-lg border border-white/10 bg-[#171a22] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
              />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-slate-200"
                >
                  Contraseña
                </label>

                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="text-xs font-medium text-cyan-400 transition hover:text-cyan-300"
                >
                  {showPassword ? "Ocultar" : "Mostrar"}
                </button>
              </div>

              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Ingrese su contraseña"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                required
                className="w-full rounded-lg border border-white/10 bg-[#171a22] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
              />
            </div>

            {mode === "register" && (
              <div>
                <label
                  htmlFor="rol"
                  className="mb-2 block text-sm font-medium text-slate-200"
                >
                  Perfil de usuario
                </label>

                <select
                  id="rol"
                  value={rol}
                  onChange={(event) => setRol(event.target.value as Rol)}
                  className="w-full rounded-lg border border-white/10 bg-[#171a22] px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                >
                  {Object.entries(ROLES_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {error && (
              <Alert variant="error">
                <span className="text-slate-900">{error}</span>
              </Alert>
            )}

            {success && (
              <Alert variant="success">
                <span className="text-slate-900">{success}</span>
              </Alert>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-cyan-400 px-5 py-3.5 text-sm font-bold text-[#0d1016] shadow-lg shadow-cyan-400/10 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting
                ? "Procesando..."
                : mode === "login"
                  ? "Entrar al sistema"
                  : "Crear cuenta"}
            </button>
          </form>

          <p className="mt-8 border-t border-white/10 pt-5 text-center text-xs leading-5 text-slate-500">
            El acceso y la información clínica están protegidos mediante
            controles de usuario.
          </p>
        </div>
      </section>

      <section
        className="relative hidden min-h-screen overflow-hidden bg-cover bg-center lg:block"
        style={{ backgroundImage: `url(${medicalImage})` }}
        aria-label="Profesional de salud utilizando el sistema"
      >
        <div className="absolute inset-0 bg-[#07131a]/45" />
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#07131a] via-[#07131a]/70 to-transparent px-10 pb-10 pt-32">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-cyan-300">
            Tecnología para cuidar
          </p>

          <h3 className="max-w-lg text-3xl font-bold leading-tight text-white">
            Toda la información clínica organizada en un solo lugar.
          </h3>

          <p className="mt-4 max-w-lg text-sm leading-6 text-slate-200">
            Gestione pacientes, citas, recetas, historial clínico y atención de
            urgencias desde una plataforma centralizada.
          </p>
        </div>
      </section>
    </main>
  );
}
