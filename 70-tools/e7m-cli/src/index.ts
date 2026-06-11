import { Command } from 'commander';
import { agentCmd } from './commands/agent.js';
import { actorCmd } from './commands/actor.js';
import { contractCmd } from './commands/contract.js';
import { graphCmd } from './commands/graph.js';
import { devCmd } from './commands/dev.js';
import { doctorCmd } from './commands/doctor.js';
import { didCmd } from './commands/did.js';
import { councilCmd } from './commands/council.js';
import { charterCmd } from './commands/charter.js';
import { govCmd } from './commands/gov.js';

const program = new Command();

program
  .name('e7m')
  .description('Etzhayyim Monorepo Unified CLI (binary alias of etzhayyim)')
  .version('0.2.0');

program.addCommand(agentCmd);
program.addCommand(actorCmd);
program.addCommand(contractCmd);
program.addCommand(graphCmd);
program.addCommand(devCmd);
program.addCommand(doctorCmd);
program.addCommand(didCmd);
program.addCommand(councilCmd);
program.addCommand(charterCmd);
program.addCommand(govCmd);

program.parseAsync(process.argv);
