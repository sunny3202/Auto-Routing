export const apiFetch = async (
  url: string,
  method: "GET" | "POST" | "PUT" | "DELETE" = "GET",
  body?: object | FormData,
  onUnauthorized?: () => void
) => {
  try {
    const token =
      document.cookie
        .split("; ")
        .find((row) => row.startsWith("access="))
        ?.split("=")[1] || "";
    console.log("Token:", token);
    const applyBody = body
      ? body instanceof FormData
        ? body
        : JSON.stringify(body)
      : undefined;
    console.log("origin Body:", body);
    console.log("Body:", applyBody);

    const response = await fetch(url, {
      method,
      credentials: "include",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: applyBody,
    });
    console.log("res", response)

    if (!response.ok) {
      if (response.status != 200 && onUnauthorized) {
        console.error("Unauthorized! Redirecting to login...");
        onUnauthorized();
      }
    }

    return await response.json();
  } catch (error) {
    console.error("API Fetch Error:", error);
    throw error;
  }
};

export default apiFetch;
