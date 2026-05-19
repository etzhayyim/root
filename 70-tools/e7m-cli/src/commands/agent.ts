import { Command } from 'commander';
import { execa } from 'execa';
import path from 'path';

export const agentCmd = new Command('agent')
  .description('Manage LangGraph AI Agents');

agentCmd
  .command('dev [project]')
  .description('Start LangGraph development server and LangGraph Studio')
  .action(async (project?: string) => {
    const targetDir = project ? path.resolve(process.cwd(), `../../60-apps/${project}`) : process.cwd();
    
    console.log(`🚀 Starting LangGraph dev server for ${project || 'current directory'}...`);
    
    try {
      await execa('npx', ['@langchain/langgraph-cli', 'dev'], {
        cwd: targetDir,
        stdio: 'inherit',
      });
    } catch (error) {
      console.error('❌ LangGraph dev server exited with error.', error);
      process.exit(1);
    }
  });

agentCmd
  .command('build [project]')
  .description('Build LangGraph application')
  .action(async (project?: string) => {
    const targetDir = project ? path.resolve(process.cwd(), `../../60-apps/${project}`) : process.cwd();
    
    console.log(`📦 Building LangGraph app for ${project || 'current directory'}...`);
    
    try {
      await execa('npx', ['@langchain/langgraph-cli', 'build'], {
        cwd: targetDir,
        stdio: 'inherit',
      });
    } catch (error) {
      console.error('❌ LangGraph build exited with error.', error);
      process.exit(1);
    }
  });

agentCmd
  .command('up [project]')
  .description('Deploy LangGraph application to local Docker')
  .action(async (project?: string) => {
    const targetDir = project ? path.resolve(process.cwd(), `../../60-apps/${project}`) : process.cwd();
    
    console.log(`🐳 Starting LangGraph app for ${project || 'current directory'} in Docker...`);
    
    try {
      await execa('npx', ['@langchain/langgraph-cli', 'up'], {
        cwd: targetDir,
        stdio: 'inherit',
      });
    } catch (error) {
      console.error('❌ LangGraph up exited with error.', error);
      process.exit(1);
    }
  });
