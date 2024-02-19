import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { Umzug, SequelizeStorage } from 'umzug'
import { Sequelize } from 'sequelize'
import { validateConfig } from './config.js'
import baseLogger from './logger.js'

const logger = baseLogger.child({ filePath: fileURLToPath(import.meta.url) })

const databaseConfig = validateConfig().db

const sequelize = new Sequelize(
  databaseConfig.name,
  databaseConfig.user,
  databaseConfig.password,
  {
    dialect: 'mysql',
    host: databaseConfig.host
  }
)

export const umzug = new Umzug({
  migrations: {
    glob: ['migrations/*.{js,ts}', { cwd: path.dirname(fileURLToPath(import.meta.url)) }],
    resolve: (params) => {
      return Umzug.defaultResolver(params)
    }
  },
  context: sequelize,
  storage: new SequelizeStorage({ sequelize, tableName: 'ccm_sequelize_meta' }),
  logger: logger
})

export type Migration = typeof umzug._types.migration

if (import.meta.url === new URL(import.meta.url).pathname) {
  logger.info('Running migrations CLI...')
  umzug
    .runAsCLI()
    .then(() => logger.info('Migration tasks ran!'))
    .catch((e) =>
      logger.error('An error occured when running the migration tasks: ', e)
    )
}
