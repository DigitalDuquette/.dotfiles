const path = require('path');

module.exports = {
	stylesheet: [path.join(__dirname, 'border-print.css')],
	body_class: [],
	pdf_options: {
		format: 'Letter',
		margin: {
			top: '20mm',
			bottom: '20mm',
			left: '20mm',
			right: '20mm',
		},
		printBackground: true,
	},
	marked_options: {
		gfm: true,
	},
};
