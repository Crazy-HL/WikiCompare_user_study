export const fetchWikipediaContent = async (pageTitle) => {
	try {
		const apiUrl = `https://en.wikipedia.org/api/rest_v1/page/html/${encodeURIComponent(pageTitle)}`;
		const response = await fetch(apiUrl);
		if (!response.ok) throw new Error("Failed to fetch data");
		return await response.text();
	} catch (err) {
		throw new Error("Error fetching Wikipedia content: " + err.message);
	}
};

export const injectWikipediaStyles = () => {
	const wikipediaStyles = [
		"https://en.wikipedia.org/w/load.php?modules=site.styles",
		"https://en.wikipedia.org/w/load.php?modules=ext.cite.styles",
		"https://en.wikipedia.org/w/load.php?modules=ext.scribunto.styles",
		"https://en.wikipedia.org/w/load.php?modules=skins.vector.styles",
	];

	wikipediaStyles.forEach((url) => {
		if (!document.querySelector(`link[href="${url}"]`)) {
			const styleTag = document.createElement("link");
			styleTag.rel = "stylesheet";
			styleTag.href = url;
			document.head.appendChild(styleTag);
		}
	});
};