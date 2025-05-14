const { Octokit } = require('@octokit/rest');
const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });

exports.handler = async function(event, context) {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }

    try {
        const config = JSON.parse(event.body);
        
        // Validate config
        if (!config.target_dates || !config.time_range || !config.num_adults_range || !config.email) {
            throw new Error('Invalid configuration format');
        }

        // Get current config.json
        const { data: currentFile } = await octokit.repos.getContent({
            owner: process.env.GITHUB_OWNER,
            repo: process.env.GITHUB_REPO,
            path: 'config.json',
        });

        // Update config.json
        await octokit.repos.createOrUpdateFileContents({
            owner: process.env.GITHUB_OWNER,
            repo: process.env.GITHUB_REPO,
            path: 'config.json',
            message: 'Update configuration via web interface',
            content: Buffer.from(JSON.stringify(config, null, 2)).toString('base64'),
            sha: currentFile.sha,
            branch: 'main'
        });

        // This will trigger the GitHub Action to run with new config
        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Configuration updated successfully' })
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Failed to update configuration' })
        };
    }
};
